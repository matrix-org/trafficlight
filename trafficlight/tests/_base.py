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
import unittest
import uuid
from enum import Enum
from typing import List

import trafficlight.homerunner
from trafficlight.homerunner import HomeserverConfig
from trafficlight.store import Model
from trafficlight.store import Client

class ClientType(object):
    def match(self, x: Client) -> bool:
        pass

class ElementWeb(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-web"


class ElementAndroid(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-android"


class BaseTestCase(unittest.TestCase):

    def __init__(self):
        self.test_id = str(uuid.uuid4())

    def validate_results(self, model: Model) -> None:
        """
        Validate the results; use unittest asserts to return success/failure/skipped etc.
        """
        pass


class TwoClientsOneServerTestCase(BaseTestCase):

    def __init__(self, client_type_one: ClientType, client_type_two: ClientType):
        super(TwoClientsOneServerTestCase, self).__init__()
        self.client_type_one: ClientType = client_type_one
        self.client_type_two = client_type_two

    def crumble(self, available_clients: List[Client]) -> List[Client]:

        # there's a better way to do this for N clients.
        one_clients: List[Client] = list(
            filter(self.client_type_one.match, available_clients)
        )
        two_clients: List[Client] = list(
            filter(self.client_type_two.match, available_clients)
        )
        for red_client in one_clients:
            for green_client in two_clients:
                if red_client != green_client:
                    # clients identified; store internally for use, return to indicate they were used.
                    self.client_one = red_client
                    self.client_two = green_client
                    return [red_client, green_client]

    def generate_model(self, homeserver: HomeserverConfig) -> Model:
        pass
