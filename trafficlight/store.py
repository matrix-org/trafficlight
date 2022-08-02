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
from typing import Any, Callable, List, Dict, Optional
from uuid import UUID

from transitions.extensions import GraphMachine  # type: ignore
from transitions.extensions.states import Timeout, add_state_features  # type: ignore

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class ModelState(object):
    def __init__(self, name: str, action_map: Dict[str, Dict[str, Any]]) -> None:
        self.name = name
        self.action_map = action_map


class Model(object):
    def __init__(self, uuid: UUID, state_list: List[ModelState], initial_state: str) -> None:
        self.uuid = uuid
        self.state = initial_state
        states = []
        state_map: Dict[str, ModelState] = {}
        for state in state_list:
            states.append(state.name)
            state_map[state.name] = state

        self.machine = GraphMachine(model=self, states=states, initial=initial_state)

        self.state_map = state_map
        self.generic_action = {"action": "idle", "responses": []}
        self.completed = False

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
                for action_name, destination in action["responses"].items():
                    logger.info(
                        "Adding %s - %s_%s -> %s", name, colour, action_name, destination
                    )
                    self.machine.add_transition(colour + "_" + action_name, name, destination)

    def transition(self, colour: str, update: Dict[str, Any]) -> None:

        transition = colour + "_" + update["response"]
        old_state = self.state
        self.trigger(transition) # type: ignore
        new_state = self.state
        logger.info(
            "State transition %s to %s ( via %s )", old_state, new_state, transition
        )

    def render_whole_graph(self, bytesio: BytesIO) -> None:
        self.get_graph().draw(bytesio, format="png", prog="dot") # type: ignore

    def render_local_region(self, bytesio: BytesIO) -> None:
        self.get_graph(show_roi=True).draw(bytesio, format="png", prog="dot") # type: ignore

    def on_enter_completed(self) -> None:
        # for client in self.clients:
        #     client.complete()
        # TODO: perhaps tell the test case it's completed instead of the clients
        # and let that percolate down?
        self.completed = True


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
            return {"action": "idle", "responses": []}

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

    def respond(self, update: Dict[str, Any], update_last_responded: bool = True) -> None:
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
    def __init__(self, uuid: UUID, description: str, client_matchers: List[Callable[[Client], bool]],
                 model_generator: Callable[[List[Client]], Model]) -> None:
        self.uuid = uuid
        self.description = description
        self.client_matchers = client_matchers
        self.model_generator = model_generator
        self.registered = datetime.now()
        self.running = False
        self.model: Optional[Model] = None

    def __str__(self) -> str:
        return f"TestCase {self.description} {self.uuid} Model {self.model} Running {self.running}"

    # takes a client list and returns clients required to run the test
    def runnable(self, client_list: List[Client]) -> Optional[List[Client]]:
        if len(self.client_matchers) == 2:
            # there's a better way to do this for N clients.
            red_clients: List[Client] = list(filter(self.client_matchers[0], client_list))
            green_clients: List[Client] = list(filter(self.client_matchers[1], client_list))

            if len(red_clients) > 0:
                for red_client in red_clients:
                    for green_client in green_clients:
                        if red_client != green_client:
                            return [red_client, green_client]

        return None

    def run(self, client_list: List[Client]) -> None:
        if self.running:
            raise Exception("Logic error: already running this test")
        else:
            self.running = True
        # tidy this up somewhat
        self.model = self.model_generator(client_list)


@add_state_features(Timeout)
class TimeoutGraphMachine(GraphMachine):  # type: ignore
    pass


clients: List[Client] = []
tests: List[TestCase] = []


def get_tests() -> List[TestCase]:
    return tests


def get_test(uuid: str) -> Optional[TestCase]:
    for test in tests:
        if str(test.uuid) == str(uuid):
            return test
        else:
            logger.info("%s did not match %s", test.uuid, uuid)
    return None


def add_test(test: TestCase) -> None:
    tests.append(test)


def get_clients() -> List[Client]:
    return clients


def get_client(uuid: str) -> Optional[Client]:
    for client in get_clients():
        if client.uuid == uuid:
            return client
    return None


def add_client(client: Client) -> None:
    clients.append(client)


# Probably move me elsewhere soon...

# I think, actually, that we can just import from json all the below as little test cases.
# But for now: this.


RED = "red"
GREEN = "green"


def generate_model(used_clients: List[Client]) -> Model:
    red_client = used_clients[0]
    green_client = used_clients[1]
    import uuid as guid

    random_user = "user_" + str(guid.uuid4())
    logging.info("User for test " + random_user)
    login_data = {
        "username": random_user,
        "password": "bubblebobblebabble",
        "homeserver_url": {
            "local_docker": "http://10.0.2.2:8080/",
            "local": "http://localhost:8080/",
        },
    }
    model = Model(
        guid.uuid4(),
        [
            ModelState(
                "init_r",
                {
                    RED: {
                        "action": "register",
                        "data": login_data,
                        "responses": {"registered": "init_g"},
                    },
                },
            ),
            ModelState(
                "init_g",
                {
                    GREEN: {
                        "action": "login",
                        "data": login_data,
                        "responses": {"loggedin": "start_crosssign"},
                    }
                },
            ),
            ModelState(
                "start_crosssign",
                {
                    GREEN: {
                        "action": "start_crosssign",
                        "responses": {"started_crosssign": "accept_crosssign"},
                    }
                },
            ),
            ModelState(
                "accept_crosssign",
                {
                    RED: {
                        "action": "accept_crosssign",
                        "responses": {"accepted_crosssign": "verify_crosssign_rg"},
                    }
                },
            ),
            ModelState(
                "verify_crosssign_rg",
                {
                    RED: {
                        "action": "verify_crosssign_emoji",
                        "responses": {"verified_crosssign": "verify_crosssign_g"},
                    },
                    GREEN: {
                        "action": "verify_crosssign_emoji",
                        "responses": {"verified_crosssign": "verify_crosssign_r"},
                    },
                },
            ),
            ModelState(
                "verify_crosssign_r",
                {
                    RED: {
                        "action": "verify_crosssign_emoji",
                        "responses": {"verified_crosssign": "complete"},
                    }
                },
            ),
            ModelState(
                "verify_crosssign_g",
                {
                    GREEN: {
                        "action": "verify_crosssign_emoji",
                        "responses": {"verified_crosssign": "complete"},
                    }
                },
            ),
            ModelState(
                "complete",
                {
                    RED: {"action": "exit", "responses": []},
                    GREEN: {"action": "exit", "responses": []},
                },
            ),
        ],
        "init_r",
    )
    model.calculate_transitions()

    red_client.set_colour(RED)
    red_client.set_model(model)
    green_client.set_colour(GREEN)
    green_client.set_model(model)
    return model
