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

import logging
import typing
import uuid
from typing import Any, Dict, List, Optional

import aiohttp
from quart import Config

from trafficlight.internals.test import Test

if typing.TYPE_CHECKING:
    from trafficlight.internals.testcase import TestCase
    from trafficlight.internals.testsuite import TestSuite

logger = logging.getLogger(__name__)

# I think this is a default. If not then we need to do some lookups on start etc.
AUTOMATED = 3
STATUS_MAP = {
    "success": 1,
    "failed": 5,
    "error": 5,  # maybe 4 = "retest"
}


class TestRailRunResult(object):
    def __init__(self, response: Dict[str, Any]):
        self.untested_count = response["untested_count"]


class TestRailException(Exception):
    pass


client: Optional[TestRailClient]


def init_testrail(config: Config) -> None:
    if config.get("TESTRAIL_API_KEY"):
        global client
        client = TestRailClient(
            config.get("TESTRAIL_URL"),
            config.get("TESTRAIL_USER"),
            config.get("TESTRAIL_API_KEY"),
            config.get("TESTRAIL_PROJECT_ID"),
        )


class TestRailClient(object):
    def __init__(
        self, testrail_url: str, user: str, api_key: str, project: int
    ) -> None:
        self.url = testrail_url
        self.authentication = aiohttp.BasicAuth(user, api_key)
        self.project = project
        self.run_id: Optional[str] = None
        self.automation_ids: Dict[str, str] = {}
        self.section_ids: Dict[str, str] = {}

    async def start_run(self) -> None:
        guid = str(uuid.uuid4())

        data = {"name": f"trafficlight {guid}"}
        begin_url = f"{self.url}/index.php?/api/v2/add_run/{self.project}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                begin_url, json=data, auth=self.authentication
            ) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                self.run_id = json["id"]

    async def build_mappings(self) -> None:
        # map GUID -> test case info here
        self.automation_ids = {}
        self.section_ids = {}

        get_suites_url = f"{self.url}/index.php?/api/v2/get_suites/{self.project}"

        self.suite_ids: List[int] = []

        async with aiohttp.ClientSession() as session:

            async with session.get(get_suites_url, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                # NB: no pagination on this API call
                if len(json) > 1:
                    raise TestRailException("Too many suites in this project")
                else:
                    self.suite_id = json[0]["id"]

            get_cases_url = f"{self.url}/index.php?/api/v2/get_cases/{self.project}"
            async with session.get(get_cases_url, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()

                if json["size"] >= json["limit"]:
                    raise TestRailException(
                        f"Finally we have > {json['size']} tests and must paginate"
                    )
                    # TODO: if we got over the pagination size, paginate with more vigour

                for case in json["cases"]:
                    self.automation_ids[case["custom_automation_id"]] = case["id"]

            get_sections_url = (
                f"{self.url}/index.php?/api/v2/get_sections/{self.project}"
            )
            async with session.get(get_sections_url, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()

                if json["size"] >= json["limit"]:
                    raise TestRailException(
                        f"Finally we have > {json['size']} tests and must paginate"
                    )
                    # TODO: if we got over the pagination size, paginate with more vigour

                for section in json["sections"]:
                    self.section_ids[section["name"]] = section["id"]

    async def prepare_sections_and_cases(self, suites: List[TestSuite]) -> None:
        for suite in suites:
            for case in suite.test_cases:
                await self.get_automation_id_for_test_case(case, create_if_missing=True)

    async def get_or_create_section(self, test: Test) -> str:
        if not test.name() in self.section_ids:
            self.section_ids[test.name()] = await self.make_section(test)

        return self.section_ids[test.name()]

    async def make_section(self, test: Test) -> str:
        # We know it doesn't exist in testrail; therefore create a new one
        data = {"suite_id": self.suite_id, "name": f"{test.name()}", "parent": None}

        add_section_url = f"{self.url}/index.php?/api/v2/add_section/{self.project}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                add_section_url, json=data, auth=self.authentication
            ) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                return str(json["id"])

    async def make_test_case(self, test_case: TestCase) -> str:
        # We know it doesn't exist in testrail; therefore create a new one
        data = {
            "title": f"{test_case.test.name()} - {test_case.server_type} {test_case.client_types}",
            "type_id": AUTOMATED,
            "custom_automation_id": test_case.guid,
        }

        section_id = await self.get_or_create_section(test_case.test)

        add_case_url = f"{self.url}/index.php?/api/v2/add_case/{section_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                add_case_url, json=data, auth=self.authentication
            ) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                return str(json["id"])

    async def get_automation_id_for_test_case(
        self, test_case: TestCase, create_if_missing: bool = False
    ) -> str:
        if test_case.guid in self.automation_ids.keys():
            return self.automation_ids[test_case.guid]

        if create_if_missing:
            test_case_id = await self.make_test_case(test_case)
            self.automation_ids[test_case.guid] = test_case_id
            return test_case_id
        else:
            raise TestRailException(
                f"Test case {test_case} should have been pre-created but was not"
            )

    async def add_test_result(self, test_case: TestCase) -> None:

        case_id = await self.get_automation_id_for_test_case(test_case)

        data = {
            "status_id": STATUS_MAP[test_case.state],
            "comment": "comment",
            "version": "version",
            "elapsed": "30s",  # " or 1m 25s"
        }
        add_result_url = (
            f"{self.url}/index.php?/api/v2/add_result_for_case/{self.run_id}/{case_id}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                add_result_url, json=data, auth=self.authentication
            ) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                await rsp.json()

    async def end_run(self) -> Optional[TestRailRunResult]:
        if self.run_id:
            close_url = f"{self.url}/index.php?/api/v2/close_run/{self.run_id}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    close_url, json={}, auth=self.authentication
                ) as rsp:
                    if rsp.status != 200:
                        error = await rsp.text()
                        raise TestRailException(error)

                    json = await rsp.json()
                    return TestRailRunResult(json)
        return None
