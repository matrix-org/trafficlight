import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trafficlight.objects.model import Model

logger = logging.getLogger(__name__)


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
        self.last_error: Optional[Dict[str, str]] = None

    def __str__(self) -> str:
        return f"Client {self.uuid} Model {self.model} Registration {self.registration}"

    def available(self) -> bool:
        return self.model is None and not self.completed

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

    def error(self, error: Dict[str, str], update_last_responded: bool = True) -> None:
        # If we error, always mark us as completed
        self.completed = True
        self.last_error = error

        logger.info("%s had an error: %s", self.uuid, str(error))

        if self.model is None or self.name is None:
            logger.info(
                "Client %s has not been assigned a model yet. Dropping error", self.uuid
            )
            return

        self.model.transition(self.name, {"response": "error", "error": error})

        if update_last_responded:
            self.last_responded = datetime.now()

    def upload(self, name: str, path: str, update_last_responded: bool = True) -> None:
        if self.model is None:
            raise Exception("Client %s has not been assigned a model yet", self.uuid)

        if self.name is None:
            raise Exception("Client not allocated a name yet")

        logger.info(
            "%s (%s) uploaded a file: %s (stored at %s)",
            self.uuid,
            self.name,
            name,
            path,
        )
        self.model.files[self.name + "_" + name] = path

        if update_last_responded:
            self.last_responded = datetime.now()

    def set_model(self, model: Model) -> None:
        logger.info("Set model %s on %s", model.uuid, self.uuid)
        self.model = model

    def set_name(self, name: str) -> None:
        logger.info("Set name %s on %s", name, self.uuid)
        self.name = name
