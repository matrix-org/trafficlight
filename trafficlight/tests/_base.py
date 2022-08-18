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
from enum import Enum

from trafficlight.homerunner import HomeserverConfig
from trafficlight.store import Model
from trafficlight.store import Client

class Style(Enum):
    """
    Style reflects the requirements for this server to be configured
    """
    TWO_CLIENTS_ONE_USER = 1
    TWO_CLIENTS_TWO_USERS_FEDERATED = 2


class BaseTestCase(unittest.TestCase):

    def style(self) -> Style:
        pass

    def validate_results(self, model: Model) -> None:
        """
        Validate the results; use unittest asserts to return success/failure/skipped etc.
        """
        pass


class TwoClientsOneServerTestCase(BaseTestCase):
    def generate_model(self, homeserver: HomeserverConfig, client_one: Client, client_two: Client) -> Model:
        pass


class TwoClientsTwoServersFederationTestCase(BaseTestCase):
    def generate_model(self, homeserver_one: HomeserverConfig, homeserver_two: HomeserverConfig, client_one: Client, client_two: Client) -> Model:

        pass