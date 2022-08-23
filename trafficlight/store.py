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
from datetime import datetime
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from transitions.extensions import GraphMachine  # type: ignore
from transitions.extensions.states import Timeout, add_state_features  # type: ignore

from trafficlight.homerunner import HomerunnerClient, HomeserverConfig

from trafficlight.client_types import ClientType
from trafficlight.server_types import ServerType
from trafficlight.tests import TestSuite

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

class ModelState(object):
    def __init__(self, name: str, action_map: Dict[str, Dict[str, Any]]) -> None:
        self.name = name
        self.action_map = action_map


class Model(object):
    def __init__(
            self, uuid: str, state_list: List[ModelState], initial_state: str, validator: Callable
    ) -> None:
        self.uuid = uuid
        self.state = initial_state
        states = []
        state_map: Dict[str, ModelState] = {}
        for state in state_list:
            states.append(state.name)
            state_map[state.name] = state

        self.machine = GraphMachine(model=self, states=states, initial=initial_state)

        self.state_map = state_map
        self.generic_action = {
            "action": "idle",
            "responses": [],
            "data": {"delay": 5000},
        }
        self.validator = validator

    def __str__(self) -> str:
        return f"Model {self.uuid}"

    def action_for_colour(self, colour: str) -> Dict[str, Any]:
        state_obj = self.state_map.get(self.state)
        if state_obj is not None:
            action_map = state_obj.action_map
            specific_action = action_map.get(colour)
            if specific_action is not None:
                return specific_action
        return self.generic_action

    def calculate_transitions(self) -> None:
        for name, state in self.state_map.items():
            for colour, action in state.action_map.items():
                logging.info(action["responses"])
                for action_name, destination in action["responses"].items():
                    logger.info(
                        "Adding %s - %s_%s -> %s",
                        name,
                        colour,
                        action_name,
                        destination,
                    )
                    self.machine.add_transition(
                        colour + "_" + action_name, name, destination
                    )

    def transition(self, colour: str, update: Dict[str, Any]) -> None:

        transition = colour + "_" + update["response"]
        old_state = self.state
        self.trigger(transition)  # type: ignore
        new_state = self.state
        logger.info(
            "State transition %s to %s ( via %s )", old_state, new_state, transition
        )

    def render_whole_graph(self, bytesio: BytesIO) -> None:
        self.get_graph().draw(bytesio, format="png", prog="dot")  # type: ignore

    def render_local_region(self, bytesio: BytesIO) -> None:
        self.get_graph(show_roi=True).draw(bytesio, format="png", prog="dot")  # type: ignore

    def on_enter_completed(self) -> None:
        # Call the validator from the testcase.
        self.validator(self)


class Client(object):
    def __init__(self, uuid: str, registration: Dict[str, Any]) -> None:
        self.colour: Optional[str] = None
        self.uuid = uuid
        self.registration = registration
        self.model: Optional[Model] = None
        self.last_polled: Optional[datetime] = None
        self.last_responded: Optional[datetime] = None
        self.registered = datetime.now()
        self.completed = False

    def __str__(self) -> str:
        return f"Client {self.uuid} Model {self.model} Registration {self.registration}"

    def poll(self, update_last_polled: bool = True) -> Dict[str, Any]:
        if self.model is None:
            # No model has been allocated yet; idle.
            return {"action": "idle", "responses": [], "data": {"delay": 30000}}

        if self.completed:
            # Client has finished work, exit
            return {"action": "exit", "responses": []}

        if self.colour is None:
            raise Exception("Client not allocated a colour yet")
        action = self.model.action_for_colour(self.colour)
        # action is some json
        if action is None:
            action = {"action": "unexpected", "responses": []}
        colour = self.colour
        logger.info("%s (%s) polled: %s", self.uuid, colour, action)
        if update_last_polled:
            self.last_polled = datetime.now()
        return action

    def respond(
            self, update: Dict[str, Any], update_last_responded: bool = True
    ) -> None:
        if self.model is None:
            raise Exception("Client %s has not been assigned a model yet", self.uuid)

        if self.colour is None:
            raise Exception("Client not matched into a model yet")
        logger.info("%s (%s) responded: %s", self.uuid, self.colour, update)
        self.model.transition(self.colour, update)
        if update_last_responded:
            self.last_responded = datetime.now()

    def set_model(self, model: Model) -> None:
        logger.info("Set model %s on %s", model.uuid, self.uuid)
        self.model = model

    def set_colour(self, colour: str) -> None:
        logger.info("Set colour %s on %s", colour, self.uuid)
        self.colour = colour

    def complete(self) -> None:
        self.completed = True


class TestCase(object):
    def __init__(
            self,
            uuid: UUID,
            description: str,
            client_types: List[ClientType],
            server_type: ServerType,
            model_generator: Callable,
    ) -> None:
        self.uuid = uuid
        self.description = description
        self.client_types = client_types
        self.server_type = server_type
        self.model_generator = model_generator
        self.registered = datetime.now()
        self.model: Optional[Model] = None
        self.time = 0
        self.status = "waiting"

    def __str__(self) -> str:
        return f"TestCase {self.description} {self.uuid} Model {self.model} Running {self.running}"

    def combine(self, available_clients: List[Client], used_clients: List[Client],
                client_types: List[ClientType]) -> bool:
        # Current target
        client_type = client_types.pop(0)
        # Find all possible matches
        matching_clients = filter(lambda x: client_type.match(x), available_clients)

        # For each possible match, evaluate if the remaining client_types are a good match
        for client in matching_clients:
            # Move client under test into used client_types
            available_clients.remove(client)
            used_clients.append(client)

            if len(client_types) == 0:
                # If have a client in hand and we have zero remaining matches to test, return true
                return True
            else:
                # We have further matches to attempt:
                if self.combine(available_clients, used_clients, client_types):
                    # We found a good match downstream (used_clients is now good)
                    return True
                else:
                    # We found no match, restore state and continue...
                    available_clients.append(client)
                    used_clients.remove(client)
                    # continue to check...
        return False

    # takes a client list and returns client_types required to run the test
    def runnable(self, client_list: List[Client]) -> Optional[List[Client]]:
        available_clients = client_list.copy()
        client_types = self.client_types.copy()
        used_clients = []
        # combine modifies the lists, so we ensure copies are passed in
        if self.combine(available_clients, used_clients, client_types):
            return used_clients
        else:
            return None

    def run(self, client_list: List[Client]) -> None:
        if self.status != "waiting":
            raise Exception("Logic error: already running this test")
        else:
            self.status = "running"

        # create server_types according to the server_types
        server_list = self.server_type.create(homerunner)
        # generate model given server config and selected client_types
        self.model = self.generate_model(client_list, server_list)


@add_state_features(Timeout)
class TimeoutGraphMachine(GraphMachine):  # type: ignore
    pass


clients: List[Client] = []
testsuites: List[TestSuite] = []


def get_testsuite(uuid: str) -> Optional[TestSuite]:
    for testsuite in testsuites:
        if str(testsuite.uuid) == str(uuid):
            return testsuite
    return None


def get_test(testsuite_uuid: str, uuid: str) -> Optional[TestCase]:
    get_testsuite(testsuite_uuid)
    for test in tests:
        if str(test.uuid) == str(uuid):
            return test
    return None


def add_testsuite(testsuite: TestSuite) -> None:
    testsuites.append(testsuite)


def get_clients() -> List[Client]:
    return clients


def get_client(uuid: str) -> Optional[Client]:
    for client in get_clients():
        if client.uuid == uuid:
            return client
    return None


def add_client(client: Client) -> None:
    clients.append(client)