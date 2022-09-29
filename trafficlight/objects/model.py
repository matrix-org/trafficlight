import logging
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional

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

        # always have an error state
        states.append("error")

        self.machine = GraphMachine(model=self, states=states, initial=initial_state)

        self.state_map = state_map
        self.generic_action = {
            "action": "idle",
            "responses": [],
            "data": {"delay": 5000},
        }
        self.error_action = {
            "action": "exit",
            "responses": [],
            "data": {},
        }
        self.completed_callback: Callable[[], str] = None
        self.responses: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.files: Dict[str, str] = {}

    def __str__(self) -> str:
        return f"Model {self.uuid}"

    def action_for_colour(self, colour: str) -> Dict[str, Any]:
        state_obj = self.state_map.get(self.state)
        if state_obj is not None:
            action_map = state_obj.action_map
            specific_action = action_map.get(colour)
            if specific_action is not None:
                return specific_action
        if self.state == "error":
            return self.error_action
        else:
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
        # permit 'error' to always transition to error.
        self.machine.add_transition("error", "*", "error")

    def error(self, colour: str, error: Dict[str, Any]) -> None:
        logger.info(f"Failing test due to client-side error {error}")
        self.trigger("error")  # type: ignore

    def transition(self, colour: str, update: Dict[str, Any]) -> None:
        if "data" in update:
            if colour in self.responses:
                self.responses[colour].update(update["data"])
            else:
                self.responses[colour] = update["data"]
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

    def on_enter_error(self) -> None:
        self.on_enter_complete()

    def on_enter_complete(self) -> None:

        if self.completed_callback is not None:
            logger.info("Test completed, running validator")
            self.completed_callback()
        else:
            logger.info("Test completed, no validator to run.")
