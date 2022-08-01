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
import uuid
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# Urgh, refactor so there's a list of client matches, and the model_generator takes a list of clients in the same order.
# Additionally, refactor so matchers are more descriptive and can explain why the test isn't running
# Maybe a hamcrest/matcher but for python type thing would do well here


class TestCase(object):
    def __init__(self, description, client_matchers, model_generator):
        self.uuid = uuid.uuid4()
        self.description = description
        self.client_matchers = client_matchers
        self.model_generator = model_generator
        self.registered = datetime.now()
        self.running = False
        self.model = None

    def __str__(self):
        return f"TestCase {self.description} {self.uuid} Model {self.model} Running {self.running}"

    # takes a client list and returns clients required to run the test
    def runnable(self, client_list):
        if len(self.client_matchers) == 2:
            # there's a better way to do this for N clients.
            red_clients = list(filter(self.client_matchers[0], client_list))
            green_clients = list(filter(self.client_matchers[1], client_list))

            if len(red_clients) > 0:
                for red_client in red_clients:
                    for green_client in green_clients:
                        if red_client != green_client:
                            return [red_client, green_client]

        return None

    def run(self, client_list):
        if self.running:
            raise Exception("Logic error: already running this test")
        else:
            self.running = True
        # tidy this up somewhat
        self.model = self.model_generator(client_list)
