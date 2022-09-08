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
import glob
import importlib
import logging
import os
import uuid
from datetime import datetime
from itertools import product
from typing import Callable, List, Optional, Tuple

import trafficlight.homerunner
from trafficlight.client_types import ClientType, NetworkProxy
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model
from trafficlight.server_types import ServerType
from trafficlight.tests.assertions import TestException

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
        network_proxy_type: ClientType,
        model_generator: Callable[[List[Client], List[HomeserverConfig], Optional[Client]], Model],
        model_validator: Callable[[Model], None],
    ) -> None:
        self.error: Optional[Exception] = None
        self.client_list: Optional[List[Client]] = None
        self.uuid = uuid
        self.description = description
        self.client_types: List[ClientType] = client_types
        self.server_type: ServerType = server_type
        self.network_proxy_type: ClientType = network_proxy_type
        self.model_generator: Callable[
            [List[Client], List[HomeserverConfig], Optional[Client]], Model
        ] = model_generator
        self.model_validator: Callable[[Model], None] = model_validator
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

    def completed_callback(self) -> str:

        try:
            logger.info(f"Found validator {self.model_validator}")
            self.model_validator(self.model)
            self.status = "success"

        except TestException as e:
            self.status = "failure"
            self.error = e
        except Exception as e2:
            self.status = "error"
            self.error = e2

        for client in self.client_list:
            client.completed = True

        logger.info(
            f"Validation complete: test was {self.status} with error {self.error}"
        )
        return self.status

    # takes a client list and returns client_types required to run the test
    def runnable(
        self, client_list: List[Client]
    ) -> Tuple[List[Client], Optional[Client]]:

        available_clients = client_list.copy()
        client_types = self.client_types.copy()
        network_proxy: Client = None
        if self.network_proxy_type:
            matching_network_proxies = list(
                filter(lambda x: self.network_proxy_type.match(x), available_clients)
            )
            if len(matching_network_proxies) > 1:
                network_proxy = matching_network_proxies[0]
            else:
                return None

        # combine modifies the lists, so we ensure copies are passed in
        accepted_clients = self.combine(available_clients, client_types)
        if accepted_clients is not None:
            return accepted_clients, network_proxy
        else:
            return None

    async def run(
        self, client_list: List[Client], network_proxy: Optional[Client]
    ) -> None:
        if self.status != "waiting":
            raise Exception("Logic error: already running this test")
        else:
            self.status = "serversetup"

        # create server_types according to the server_types
        try:
            server_list = await self.server_type.create(self.uuid, homerunner)
        except Exception as e:
            self.error = e
            self.status = "error"
            return

        self.status = "clientsetup"

        client_name = 0
        for client in client_list:
            client.name = _CLIENT_NAMES[client_name]
            client_name = client_name + 1

        # generate model given server config and selected client_types
        try:
            self.model = self.model_generator(client_list, server_list, network_proxy)
        except Exception as e:
            self.error = e
            self.status = "error"
            return

        self.model.uuid = self.uuid
        self.model.completed_callback = self.completed_callback
        self.client_list = client_list

        for client in client_list:
            client.set_model(self.model)

        network_proxy.set_model(self.model)

        self.status = "running"
        logger.info("Test case setup and ready to run")


class TestSuite(object):
    def __init__(self) -> None:
        self.uuid = str(uuid.uuid4())
        self.test_cases: Optional[List[TestCase]] = None
        self.client_types: Optional[List[ClientType]] = None
        self.server_types: Optional[List[ServerType]] = None
        self.clients_needed = 0
        self.servers_needed = 0
        self.network_proxy_needed = False

    def name(self) -> str:
        return self.__class__.__name__

    def generate_model(
        self,
        clients: List[Client],
        homeservers: List[HomeserverConfig],
        network_proxy: Optional[Client],
    ) -> Model:
        pass

    def validate_model(self, model: Model) -> None:
        raise TestException("No validation method found")

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
                logger.info(f"Using validation method {self.validate_model}")
                validator = self.validate_model
                name = self.__class__.__name__ + "_" + client_names + "_" + server_names
                guid = str(uuid.uuid4())

                logger.info(
                    f"Creating test {name}\n"
                    f" UUID: {guid}\n"
                    f" Clients: {[x.name() for x in client_type_list]}\n"
                    f" Servers: {[x.name() for x in server_type_list]}\n"
                )

                network_proxy = NetworkProxy() if self.network_proxy_needed else None

                test_cases.append(
                    TestCase(
                        guid,
                        name,
                        list(client_type_list),
                        server_type_list[0],
                        network_proxy,
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


def load_test_suites(
    pattern: str,
    server_type_str: List[str],
    client_type_str: List[str],
    base_path: str = "./trafficlight/tests",
) -> List[TestSuite]:
    server_types: List[ServerType] = list(
        map(lambda x: getattr(trafficlight.server_types, x)(), server_type_str)  # type: ignore
    )
    client_types: List[ClientType] = list(
        map(lambda x: getattr(trafficlight.client_types, x)(), client_type_str)  # type: ignore
    )
    logger.info(f"Converted {server_type_str} to {server_types}")
    logger.info(f"Converted {client_type_str} to {client_types}")
    # base_path is like "trafficlight/tests"
    globber = base_path + "/" + pattern
    files = glob.glob(globber, recursive=True)
    # files is like ["trafficlight/tests/send_messages_testsuite.py",...]
    logger.info(f"Converting {globber} into {len(files)} files")
    test_suites: List[TestSuite] = []
    for file in files:
        parts = file.split(os.sep)
        # Convert a filename into a module name ("send_messages_testsuite.py" -> "send_messages_testsuite")
        file = parts[-1]
        file = file.replace(".py", "", 1)
        # Ignore leading "." ([".","trafficlight","tests"] -> ["trafficlight","tests"])
        path = parts[1:-1]
        # Finally combine into a full module name (trafficlight.tests.send_messages_testsuite)
        module = ".".join(path) + "." + file
        test_suites.extend(
            load_test_suites_from_module(module, server_types, client_types)
        )

    return test_suites


def load_test_suites_from_module(
    module_name: str, server_types: List[ServerType], client_types: List[ClientType]
) -> List[TestSuite]:
    module = importlib.import_module(module_name)
    test_suites: List[TestSuite] = []
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, TestSuite)
            and not isinstance(obj, TestSuite)
        ):
            logger.info(f"Found TestSuite {obj}")
            test_suite: TestSuite = obj()
            test_suite.server_types = server_types
            test_suite.client_types = client_types
            test_suites.append(test_suite)

    return test_suites
