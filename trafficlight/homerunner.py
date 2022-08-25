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
from typing import Any, Dict, List

import aiohttp

logger = logging.getLogger(__name__)


class HomeserverConfig(object):
    """
    The configuration of a created homserver
    """

    def __init__(self, server_name: str, cs_api: str, base_image_uri: str):
        self.cs_api = cs_api
        self.server_name = server_name
        self.base_image_uri = base_image_uri
        # TODO: include sufficient data to destroy
        # Might not be needed: homerunner does have a timeout


class HomerunnerClient(object):
    def __init__(self, homerunner_url: str) -> None:
        self.homerunner_url = homerunner_url
        self.hsid = 0

    def _generate_homeserver(self, base_image_uri: str) -> Dict[str, Any]:
        """
        For now, we don't require any Users or Rooms to be created automatically
        """
        self.hsid = self.hsid + 1
        return {
            "Name": "trafficlight" + str(self.hsid),
            "Users": [],
            "Rooms": [],
            "BaseImageURI": base_image_uri,
        }

    async def create(self, model_id: str, images: List[str]) -> List[HomeserverConfig]:
        create_url = self.homerunner_url + "/create"
        homeservers = []
        for image in images:
            homeservers.append(self._generate_homeserver(image))
        data = {
            "base_image_uri": "INVALID_NAME",  # uppercase is not a valid docker repository name, so this will cause a complement error.
            "blueprint": {"Name": model_id, "Homeservers": homeservers},
        }
        logger.info(data)
        async with aiohttp.ClientSession() as session:
            async with session.post(create_url, json=data) as rsp:

                json = await rsp.json()
                logger.info(json)

                response = json["homeservers"]
                # TODO: check responsecode etc
                homeserver_configs = []
                for homeserver in homeservers:
                    # from our request
                    name = homeserver["Name"]
                    base_image_uri = homeserver["BaseImageURI"]
                    # from response
                    cs_api = response[name]["BaseURL"]
                    homeserver_configs.append(
                        HomeserverConfig(name, cs_api, base_image_uri)
                    )
                return homeserver_configs
