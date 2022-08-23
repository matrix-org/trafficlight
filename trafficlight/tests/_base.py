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
import itertools
import unittest
import uuid
from enum import Enum
from typing import List

import trafficlight.homerunner
from trafficlight.client_types import ClientType
from trafficlight.homerunner import HomeserverConfig
from trafficlight.store import Model, TestCase, ServerType
from trafficlight.store import Client


class TestSuite(object):
    def __init__(self, name: str, testcases: List[TestCase]) -> None:
        self.name = name


class TestSuite(object):

    def __init__(self, clients_needed, servers_needed):
        self.test_cases = None
        self.client_types = None
        self.server_type = None
        self.clients_needed = clients_needed
        self.servers_needed = servers_needed

    def server_type(self, server_type: ServerType):
        self.server_type = server_type

    def client_types(self, client_types: List[ClientType]):
        self.client_types = client_types

    def generate_model(self, clients: List[Client], homeservers: List[HomeserverConfig]) -> Model:
        pass

    def validate_model(self, model: Model) -> None:
        pass

    def generate_test_cases(self) -> List[TestCase]:
        test_cases = []

        client_types_expanded = itertools.combinations_with_replacement(self.client_types, self.clients_needed)
        server_types_expanded = itertools.combinations_with_replacement(self.server_types, self.servers_needed)

        for client_type_list in client_types_expanded:
            client_names = ",".join(map(lambda x: x.__name__, client_type_list))
            for server_type_list in server_types_expanded:
                server_names = ",".join(map(lambda x: x.__name__, server_type_list))
                model = self.generate_model()

                ## ARGH hell
                def validator() -> str:
                    return self.validate_model(model)

                test_cases.append(TestCase(uuid.uuid4(),
                                           self.__name__ + client_names + server_names,
                                           client_type_list,
                                           server_type_list,
                                           model,
                                           validator),
                                  )
        self.test_cases = test_cases

        return test_cases

    def successes(self):
        return 0 + sum(1 for tc in self.test_cases if tc.status == "success")

    def failures(self):
        return 0 + sum(1 for tc in self.test_cases if tc.status == "failure")

    def errors(self):
        return 0 + sum(1 for tc in self.test_cases if tc.status == "error")

    def errors(self):
        return 0 + sum(1 for tc in self.test_cases if tc.status in ("waiting", "running", "skipped"))
