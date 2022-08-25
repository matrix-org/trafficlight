# vim: expandtab ts=4:
# Copyright 2022 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import importlib
import logging
import uuid
from datetime import datetime
from itertools import product
from typing import Callable, List, Optional

import trafficlight.homerunner
from trafficlight.client_types import ClientType, ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects import Client, Model
from trafficlight.server_types import ServerType, Synapse

_CLIENT_NAMES = ["alice", "bob", "carol", "david", "eve", "frank"]

logger = logging.getLogger(__name__)
homerunner = trafficlight.homerunner.HomerunnerClient("http://localhost:54321")


class TestCase(object):
    def __init__(
        self,
        uuid: str,
        description: str,
        client_types: List[ClientType],
        server_type: ServerType,
        model_generator: Callable[[List[Client], List[HomeserverConfig]], Model],
        validator: Callable[[Model], None],
    ) -> None:
        self.uuid = uuid
        self.description = description
        self.client_types: List[ClientType] = client_types
        self.server_type: ServerType = server_type
        self.model_generator: Callable[
            [List[Client], List[HomeserverConfig]], Model
        ] = model_generator
        self.validator = validator
        self.registered = datetime.now()
        self.model: Optional[Model] = None
        self.time = 0
        self.status = "waiting"

    def __str__(self) -> str:
        return f"TestCase {self.description} {self.uuid} Model {self.model} Status {self.status}"

    def combine(
        self, available_clients: List[Client], client_types: List[ClientType]
    ) -> Optional[List[Client]]:
        logger.info(f"{available_clients}, {client_types}")
        client_type = client_types[0]

        # Find all possible matches
        matching_clients = list(
            filter(lambda x: client_type.match(x), available_clients)
        )

        inner_client_types = client_types.copy()
        inner_client_types.remove(client_type)

        for client in matching_clients:

            if len(inner_client_types) == 0:
                # If have a client in hand and we have zero remaining matches to test, return true
                return [client]
            else:
                # We have further matches to attempt:
                inner_available_clients = available_clients.copy()
                inner_available_clients.remove(client)
                accepted_clients = self.combine(
                    inner_available_clients, inner_client_types
                )
                if accepted_clients is not None:
                    accepted_clients.append(client)
                    return accepted_clients

        return None

    # takes a client list and returns client_types required to run the test
    def runnable(self, client_list: List[Client]) -> Optional[List[Client]]:

        available_clients = client_list.copy()
        client_types = self.client_types.copy()
        # combine modifies the lists, so we ensure copies are passed in
        accepted_clients = self.combine(available_clients, client_types)
        if accepted_clients is not None:
            return accepted_clients
        else:
            return None

    def run(self, client_list: List[Client]) -> None:
        if self.status != "waiting":
            raise Exception("Logic error: already running this test")
        else:
            self.status = "running"

        client_name = 0
        for client in client_list:
            client.name = _CLIENT_NAMES[client_name]
            client_name = client_name + 1

        # create server_types according to the server_types
        server_list = self.server_type.create(self.uuid, homerunner)
        # generate model given server config and selected client_types
        self.model = self.model_generator(client_list, server_list)
        self.model.uuid = self.uuid
        for client in client_list:
            client.set_model(self.model)


class TestSuite(object):
    def __init__(self) -> None:
        self.uuid = str(uuid.uuid4())
        self.test_cases: Optional[List[TestCase]] = None
        self.client_types: Optional[List[ClientType]] = None
        self.server_types: Optional[List[ServerType]] = None
        self.clients_needed = 0
        self.servers_needed = 0

    def name(self) -> str:
        return self.__class__.__name__

    def generate_model(
        self, clients: List[Client], homeservers: List[HomeserverConfig]
    ) -> Model:
        pass

    def validate_model(self, model: Model) -> None:
        pass

    def generate_test_cases(self) -> List[TestCase]:
        test_cases = []

        # TODO: aaactually, we need to iterate all permutations of this, so [a,b] -> [(aa),(ab),(ba),(bb)]
        client_types_expanded = list(
            product(self.client_types or [], repeat=self.clients_needed)
        )
        server_types_expanded = list(
            product(self.server_types or [], repeat=self.servers_needed)
        )

        for client_type_list in client_types_expanded:

            client_names = "-".join(map(lambda x: x.name(), client_type_list))
            for server_type_list in server_types_expanded:
                server_names = "-".join(map(lambda x: x.name(), server_type_list))
                model_generator = self.generate_model
                validator = self.validate_model
                name = self.__class__.__name__ + "_" + client_names + "_" + server_names
                guid = str(uuid.uuid4())
                logger.info(
                    f"Creating test {guid}\n Name: {name}\n Clients: {client_type_list}\n Servers: {server_type_list}"
                )
                test_cases.append(
                    TestCase(
                        guid,
                        name,
                        list(client_type_list),
                        server_type_list[0],
                        model_generator,
                        validator,
                    ),
                )
        self.test_cases = test_cases

        return test_cases

    def successes(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "success")
        return 0

    def failures(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "failure")
        return 0

    def errors(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(1 for tc in self.test_cases if tc.status == "error")
        return 0

    def skipped(self) -> int:
        if self.test_cases is not None:
            return 0 + sum(
                1
                for tc in self.test_cases
                if tc.status in ("waiting", "running", "skipped")
            )
        return 0


def load_test_suites() -> List[TestSuite]:
    # TODO: iterate over packages and return big list
    # TODO: filter out unwanted server / client types
    module = importlib.import_module("trafficlight.tests.verify_client_testsuite")
    class_ = getattr(module, "VerifyClientTestSuite")

    test_suite: TestSuite = class_()
    test_suite.server_types = [
        Synapse(),
    ]
    test_suite.client_types = [
        ElementAndroid(),
        ElementWeb(),
    ]
    return [test_suite]
