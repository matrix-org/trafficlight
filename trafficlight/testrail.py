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
from typing import Any, Dict, List, Optional, Set
from trafficlight.internals.testcase import TestCase
from trafficlight.internals.test import Test
from uuid import UUID
import aiohttp

logger = logging.getLogger(__name__)

# I think this is a default. If not then we need to do some lookups on start etc.
AUTOMATED = 3
STATUS_MAP = {
    "success": 1,
    "failed": 5,
    "error": 5, # maybe 4 = "retest"

}
class TestRailRunResult(object):
    def __init__(self, response: Dict[str,Any]):
        self.untested_count = response['untested_count']
        self.run_id = response['run_id']

class TestRailException(Exception):
    pass

class TestRailClient(object):
    def __init__(self, testrail_url: str, user: str, api_key: str, project: int) -> None:
        self.url = testrail_url
        self.authentication = aiohttp.BasicAuth(user, api_key)
        self.project = project
        self.run_id: Optional[str] = None
        self.test_cases: Dict[str, Any] = None
        self.automation_ids: Dict[str, str] = {}
        self.section_ids: Dict[str, str] = {}

    async def add_run(self):
        guid = str(UUID.UUID4())

        data = { "name": f"trafficlight {guid}"}
        begin_url = f"{self.url}/index.php?/api/v2/add_run/{self.project}"

        async with aiohttp.ClientSession() as session:
            async with session.post(begin_url, json=data, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                self.run_id = json['id']

        await self.create_automation_id_mapping()

    async def build_mappings(self):
        # map GUID -> test case info here
        self.automation_ids = {}
        self.section_ids = {}

        get_url = f"{self.url}/index.php?/api/v2/get_cases/{self.project}"
        get_sections_url = f"{self.url}/index.php?/api/v2/get_sections/{self.project}"

        async with aiohttp.ClientSession() as session:
            async with session.get(get_url, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()

                if json["size"] >= json["limit"]:
                    raise TestRailException(f"Finally we have > {json['size']} tests and must paginate")
                    # TODO: if we got over the pagination size, paginate with more vigour

                for case in json["cases"]:
                    self.automation_ids[case["custom_automation_id"]] = case["id"]

            async with session.get(get_sections_url, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()

                if json["size"] >= json["limit"]:
                    raise TestRailException(f"Finally we have > {json['size']} tests and must paginate")
                    # TODO: if we got over the pagination size, paginate with more vigour

                for section in json["sections"]:
                    self.section_ids[section["name"]] = section["id"]

    async def get_or_create_section(self, test: Test):
        if test.name() in self.section_ids:
            return self.section_ids[test.name()]

        return self.make_section(test)

    async def make_section(self, test: Test) -> str:
        # We know it doesn't exist in testrail; therefore create a new one
        data = {
            "title": f"{test.name()}",
        }


        add_section_url = f"{self.url}/index.php?/api/v2/add_section/{self.project_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(add_section_url, json=data, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                return json['id']

    async def make_test_case(self, test_case: TestCase) -> str:
        # We know it doesn't exist in testrail; therefore create a new one
        data = {"title": f"{test_case.test.name()} - {test_case.server_type} {test_case.client_types}",
                "type_id": AUTOMATED,
                "custom_automation_id": test_case.guid
        }

        section_id = self.get_or_create_section(test_case.test.name())

        add_case_url = f"{self.url}/index.php?/api/v2/add_case/{section_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(add_case_url, json=data, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                return json['id']


    async def get_id_for_test_case(self, test_case) -> str:
        if test_case.guid in self.automation_ids.keys():
            return self.automation_ids[test_case.guid]

        # not present; needs creating
        return await self.make_test_case(self, test_case)

    async def add_test_result(self, test_case: TestCase):

        case_id = self.get_id_for_automation_id(test_case.guid)

        data = {
           "status_id": STATUS_MAP[test_case.state],
           "comment": "comment",
           "version": "version",
           "elapsed": "30s" # " or 1m 25s"
        }
        add_result_url = f"{self.url}/index.php?/api/v2/add_result_for_case/{self.run_id}/{case_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(add_result_url, json=data, auth=self.authentication) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                await rsp.json()

    async def end_run(self) -> TestRailRunResult:

        close_url = f"{self.url}/index.php?/api/v2/close_run/{self.run_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(close_url, json={}) as rsp:
                if rsp.status != 200:
                    error = await rsp.text()
                    raise TestRailException(error)

                json = await rsp.json()
                return TestRailRunResult(json)

