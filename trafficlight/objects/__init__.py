import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from transitions.extensions import GraphMachine  # type: ignore

logger = logging.getLogger(__name__)


class ModelState(object):
    def __init__(self, name: str, action_map: Dict[str, Dict[str, Any]]) -> None:
        self.name = name
        self.action_map = action_map


class Model(object):
    def __init__(self, state_list: List[ModelState], initial_state: str) -> None:
        self.uuid: Optional[str] = None
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
        pass
        # Call the validator from the testcase.
        # self.validator(self)
        # todo make this update the test case with results etc...


class Client(object):
    def __init__(self, uuid: str, registration: Dict[str, Any]) -> None:
        self.name = uuid
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

        if self.name is None:
            raise Exception("Client not allocated a name yet")
        action = self.model.action_for_colour(self.name)
        # action is some json
        if action is None:
            action = {"action": "unexpected", "responses": []}
        colour = self.name
        logger.info("%s (%s) polled: %s", self.uuid, colour, action)
        if update_last_polled:
            self.last_polled = datetime.now()
        return action

    def respond(
        self, update: Dict[str, Any], update_last_responded: bool = True
    ) -> None:
        if self.model is None:
            raise Exception("Client %s has not been assigned a model yet", self.uuid)

        if self.name is None:
            raise Exception("Client not allocated a name yet")
        logger.info("%s (%s) responded: %s", self.uuid, self.name, update)
        self.model.transition(self.name, update)
        if update_last_responded:
            self.last_responded = datetime.now()

    def set_model(self, model: Model) -> None:
        logger.info("Set model %s on %s", model.uuid, self.uuid)
        self.model = model

    def set_name(self, name: str) -> None:
        logger.info("Set name %s on %s", name, self.uuid)
        self.name = name

    def complete(self) -> None:
        self.completed = True
