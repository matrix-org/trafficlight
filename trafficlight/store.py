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
import logging
from typing import List, Optional

from trafficlight.internals.testcase import TestCase
from trafficlight.internals.testsuite import TestSuite
from trafficlight.objects.adapter import Adapter

logger = logging.getLogger(__name__)

_adapters: List[Adapter] = []
_testsuites: List[TestSuite] = []
_testcases: List[TestCase] = []


def get_testsuites() -> List[TestSuite]:
    return _testsuites


def get_testsuite(guid: str) -> Optional[TestSuite]:
    for testsuite in _testsuites:
        if testsuite.guid == guid:
            return testsuite
    return None


def get_tests() -> List[TestCase]:
    return _testcases


def get_test(guid: str) -> Optional[TestCase]:
    for test in _testcases:
        if str(test.guid) == str(guid):
            return test
    return None


def add_testsuite(testsuite: TestSuite) -> None:
    _testsuites.append(testsuite)
    _testcases.extend(testsuite.test_cases or [])


def get_adapters() -> List[Adapter]:
    return _adapters


def get_adapter(guid: str) -> Optional[Adapter]:
    for adapter in get_adapters():
        if adapter.guid == guid:
            return adapter
    return None


def add_adapter(adapter: Adapter) -> None:
    _adapters.append(adapter)
