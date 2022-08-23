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
from typing import List

import importlib

from trafficlight.client_types import *
from trafficlight.server_types import *
from trafficlight.tests._base import TestSuite


def get_suites() -> List[TestSuite]:
    # TODO: iterate over packages and return big list
    # TODO: filter out unwanted server / client types
    module = importlib.import_module("trafficlight.tests.verify_client_lights")
    class_ = getattr(module, "SendMessagesLights")
    test_suite: TestSuite = class_()
    test_suite.server_type(Synapse())
    test_suite.client_types([ElementAndroid(), ElementWeb()])
    return [test_suite]
