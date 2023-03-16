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
from __future__ import annotations

import asyncio
import logging
import typing
from typing import List, Optional

from tcms_api import plugin_helpers  # type: ignore

import trafficlight.store

if typing.TYPE_CHECKING:
    from trafficlight.internals.testcase import TestCase

logger = logging.getLogger(__name__)


class KiwiException(Exception):
    pass


class Backend(plugin_helpers.Backend):  # type: ignore
    name = "trafficlight"
    version = "0.0.1"  # TODO tie to TL release.


def summarize_test_case(tl_test_case: TestCase) -> str:
    """
    Summarises the given testcase into a string. Ensures that the test name is cut off first before
    we cut off the test parameters
    @param tl_test_case: Trafficlight test case to summarise
    @return: a string of up to 255 characters
    """
    postfix = f" {tl_test_case.server_type} {tl_test_case.client_types}"
    remaining = 255 - len(postfix)
    summary = f"{tl_test_case.test.name()} - "[:remaining] + postfix
    return summary


kiwi_client: Optional[KiwiClient] = None


class KiwiClient(object):
    def __init__(self, verbose: bool) -> None:
        self.backend = Backend(prefix="[trafficlight]", verbose=verbose)
        self.verbose = verbose
        self.status_error = 0
        self.status_failed = 0
        self.status_success = 0

    async def start_run(self) -> None:
        test_cases = trafficlight.store.get_tests()
        await asyncio.to_thread(self._start_run_sync, test_cases)

    def _start_run_sync(self, test_cases: List[TestCase]) -> None:

        # Create test execution etc...
        self.backend.configure()
        self._status_map = {
            "error": self.backend.get_status_id("ERROR"),
            "failed": self.backend.get_status_id("FAILED"),
            "success": self.backend.get_status_id("PASSED"),
        }

        # ensure test_cases exist in the given plan, but do not yet add them to the run.
        for tl_test_case in test_cases:
            kiwi_test_case, _ = self.backend.test_case_get_or_create(
                summarize_test_case(tl_test_case)
            )
            self.backend.add_test_case_to_plan(kiwi_test_case["id"], self.backend.plan_id)

    async def report_status(self, tl_test_case: TestCase) -> None:
        await asyncio.to_thread(self._report_status, tl_test_case)

    def _report_status(self, tl_test_case: TestCase) -> None:
        status_id = self._status_map[tl_test_case.state]
        kiwi_test_case, _ = self.backend.test_case_get_or_create(
            summarize_test_case(tl_test_case)
        )
        executions = self.backend.add_test_case_to_run(
            kiwi_test_case["id"], self.backend.run_id
        )
        comment = "Adapters:\n"
        for name, adapter in tl_test_case.adapters.items():
            adapter_details = (
                f"{name} = {adapter.client.name} {adapter.client.registration}\n"
            )
            comment += adapter_details

        comment += "Servers:\n"
        for server in tl_test_case.servers:
            server_details = f"{server.server_name} = {server.cs_api}"
            comment += server_details

        for execution in executions:
            self.backend.update_test_execution(
                execution["id"], status_id, comment=comment
            )

    async def end_run(self) -> None:
        await asyncio.to_thread(self._end_run_sync)

    def _end_run_sync(self) -> None:
        self.backend.finish_test_run()
