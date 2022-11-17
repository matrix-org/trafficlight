import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from trafficlight.internals.client import Client

logger = logging.getLogger(__name__)

class Adapter(object):
    def __init__(self, guid: str, registration: Dict[str, Any]) -> None:
        self.guid = guid
        self.registration = registration
        now = datetime.now()
        self.last_polled = now
        self.last_responded = now
        self.registered = now
        self.completed = False
        self.last_error: Optional[Exception] = None
        # After allocation to a TestCase, this becomes valid and is where
        # updates should be passed to.
        self.client: Optional[Client] = None

    def __repr__(self) -> str:
        return f"{self.guid} {self.registration}"

    def available(self) -> bool:
        return self.client is None

    def finished(self) -> None:
        self.completed = True

    def poll(self, update_last_polled: bool = True) -> Dict[str, Any]:
        if self.completed:
            action: Dict[str, Any] = {"action": "exit", "data": { "reason": "test has completed"}}
        elif self.client is None:
            # No model has been allocated yet; idle.
            action = {"action": "idle", "data": {"delay": "30000", "reason": "waiting for testcase"}}
        else:
            action = self.client._get_poll_data()

        if update_last_polled:
            self.last_polled = datetime.now()

        return action

    def respond(
        self, update: Dict[str, Any], update_last_responded: bool = True
    ) -> None:
        if self.client is None:
            raise Exception("Adapter %s has not been assigned a client yet", self.guid)

        self.client._give_poll_response(update)
        if update_last_responded:
            self.last_responded = datetime.now()

    def error(
        self,
        error: Exception,
        update_last_responded: bool = True,
    ) -> None:
        # If we error, always mark us as completed
        self.completed = True
        self.last_error = error

        logger.info("%s had an error: %s", self.guid, str(error))

        if self.client is None:
            logger.info(
                "Adapter %s has not been assigned a client yet. Dropping error",
                self.guid,
            )
            return
        if update_last_responded:
            self.last_responded = datetime.now()

        self.client._give_poll_exception(error)

    def upload(self, name: str, path: str, update_last_responded: bool = True) -> None:
        if self.client is None:
            raise Exception("Adapter %s has not been assigned a client yet", self.guid)

        logger.info(
            "%s (%s) uploaded a file: %s (stored at %s)",
            self.guid,
            self.client.name,
            name,
            path,
        )
        # TODO link up to testCase somehow
        self.client.test_case.files[self.client.name + "_" + name] = path

        if update_last_responded:
            self.last_responded = datetime.now()

    def set_client(self, client: Client) -> None:
        logger.info("Allocate adapter %s to %s", self.guid, client)
        self.client = client
