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
from typing import List

from trafficlight.internals.test import Test

_CLIENT_NAMES = [
    "alice",
    "bob",
    "carol",
    "david",
    "eve",
    "frank",
    "gertrude",
    "hannah",
    "imogen",
    "james",
    "kirk",
    "leo",
    "michael",
]

logger = logging.getLogger(__name__)


def load_tests(
    pattern: str,
    base_path: str = "./trafficlight/tests",
) -> List[Test]:
    # base_path is like "trafficlight/tests"
    globber = base_path + "/" + pattern
    files = glob.glob(globber, recursive=True)
    # files is like ["trafficlight/tests/send_messages_testsuite.py",...]
    logger.info(f"Converting {globber} into {len(files)} files")
    tests: List[Test] = []
    for file in files:
        parts = file.split(os.sep)
        # Convert a filename into a module name ("send_messages_testsuite.py" -> "send_messages_testsuite")
        file = parts[-1]
        file = file.replace(".py", "", 1)
        # Ignore leading "." ([".","trafficlight","tests"] -> ["trafficlight","tests"])
        path = parts[1:-1]
        # Finally combine into a full module name (trafficlight.tests.send_messages_testsuite)
        module = ".".join(path) + "." + file
        tests.extend(load_tests_from_module(module))

    return tests


def load_tests_from_module(module_name: str) -> List[Test]:
    module = importlib.import_module(module_name)
    tests: List[Test] = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, Test) and not obj == Test:
            logger.info(f"Found Test {obj}")
            test = obj()
            tests.append(test)

    return tests
