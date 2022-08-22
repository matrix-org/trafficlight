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
from typing import List, Any

import importlib
from inspect import signature
from trafficlight.tests._base import BaseTestCase, ElementAndroid, ElementWeb


# from trafficlight.tests.verify_client_lights import VerifyClientLights
# from trafficlight.tests.send_messages_lights import SendMessagesLights
# TODO: file based discovery?


def generateAllTests():
    module = importlib.import_module("trafficlight.tests.verify_client_lights")
    client_types = [ElementWeb, ElementAndroid]
    generateTests(module, "SendMessagesLights", client_types)


def append_to_list_of_lists(current_list, additions):
    newlist = []
    for one_list in current_list:
        newlist.extend(append_to_list(one_list, additions))
    return newlist


def append_to_list(current: List[Any], additions: List[Any]) -> List[Any]:
    newlist: List[Any] = []
    for item in additions:
        newlist.append(current.copy().append(item))
    return newlist


def generate_tests(module, test_spec: str, client_types) -> List[BaseTestCase]:
    class_ = getattr(module, test_spec)

    sig = signature(class_)
    collected_tests: List[BaseTestCase] = []
    collected_arguments = [[]]  # list of lists of arguments
    if "client_type_one" in sig.parameters.keys():
        collected_arguments = append_to_list_of_lists(collected_arguments, client_types)
    if "client_type_two" in sig.parameters.keys():
        collected_arguments = append_to_list_of_lists(collected_arguments, client_types)
    if "client_type_three" in sig.parameters.keys():
        collected_arguments = append_to_list_of_lists(collected_arguments, client_types)

    for item in collected_arguments:
        collected_tests.append(class_(*item))
    return collected_tests
