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
from typing import Any

from trafficlight.objects.model import Model

#
# Aware that we're skipping naming conventions here.
# Doing so to keep in sync with unittest -style (junit style?) conventions
# as i don't want to relearn them.
#


class TestException(Exception):
    def __init__(self, msg: str = None):
        print(msg)
        self.msg = msg
        self.state = "failure"


# noinspection PyPep8Naming
def assertEqual(first: Any, second: Any, msg: str = "") -> None:
    if first != second:
        raise TestException(f"{first} is not {second} {msg}")


# noinspection PyPep8Naming
def assertNotNone(first: Any, msg: str = "") -> None:
    if first is not None:
        raise TestException(f"{first} is not None {msg}")


def assertThat(expr: Any, msg: str) -> None:
    if bool(expr):
        raise TestException(f"{msg}")


# noinspection PyPep8Naming
def assertTrue(expr: Any, msg: str = "") -> None:
    if bool(expr):
        raise TestException(f"{expr} is not True {msg}")


# noinspection PyPep8Naming


def assertFalse(expr: Any, msg: str = "") -> None:
    if not bool(expr):
        raise TestException(f"{expr} is not False {msg}")


# noinspection PyPep8Naming


def assertCompleted(model: Model) -> None:
    if model.state != "complete":
        raise TestException(f"Model not completed, still in state {model.state}")
