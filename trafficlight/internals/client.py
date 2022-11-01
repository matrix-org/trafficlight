import asyncio
import logging
from typing import Any, Dict

from trafficlight.homerunner import HomeServer

logger = logging.getLogger(__name__)

DEFAULT_POLL_RESPONSE: Dict[str, Any] = {
    "action": "idle",
    "responses": [],
    "data": {"delay": 5000},
}


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id


class Client:
    def __init__(self, name: str, test_case):
        self.name = name
        self.test_case = test_case
        # Client login details
        self.localpart = "user_" + name
        self.password = "pass_" + name

        self.current_poll_response = DEFAULT_POLL_RESPONSE
        self.current_poll_future = None

    def __repr__(self):
        return self.name

    # Called by the http client API
    def _get_poll_data(self) -> Dict[str, Any]:
        return self.current_poll_response

    # Called by the http client API
    def _give_poll_response(self, data: Dict[str, Any]):
        if self.current_poll_future is not None:
            self.current_poll_future.set_result(data)
        else:
            raise Exception("Unable to handle response; not awaiting that.")

        # resolve the promise s.t. register returns

    def _give_poll_exception(self, exception: Exception):
        self.current_poll_future.set_exception(exception)

    # used by named methods from the test
    async def _perform_action(self, question: Dict[str, Any]) -> Dict[str, Any]:
        if self.current_poll_future is not None:
            raise Exception(
                "Action collision: already waiting for response to "
                + str(self.current_poll_response)
            )

        self.current_poll_response = question
        self.current_poll_future = asyncio.get_running_loop().create_future()

        rsp = await self.current_poll_future
        self.current_poll_future = None
        self.current_poll_response = DEFAULT_POLL_RESPONSE
        return rsp

    # exposed to the test to act
    async def register(self, homeserver: HomeServer) -> None:

        url = homeserver.cs_api
        docker_api = url.replace("localhost", "10.0.2.2")

        await self._perform_action(
            {
                "action": "register",
                "data": {
                    "username": self.localpart,
                    "password": self.password,
                    "homeserver_url": {
                        "local_docker": docker_api,
                        "local": url,
                    },
                },
            }
        )

    async def login(self, homeserver: HomeServer) -> None:
        url = homeserver.cs_api
        docker_api = url.replace("localhost", "10.0.2.2")

        await self._perform_action(
            {
                "action": "login",
                "data": {
                    "username": self.localpart,
                    "password": self.password,
                    "homeserver_url": {
                        "local_docker": docker_api,
                        "local": url,
                    },
                },
            }
        )

    async def start_crosssign(self) -> None:
        await self._perform_action({"action": "start_crosssign", "data": {}})

    async def accept_crosssign(self) -> None:
        await self._perform_action({"action": "accept_crosssign", "data": {}})

    async def verify_crosssign(self) -> None:
        await self._perform_action({"action": "verify_crosssign", "data": {}})

    async def create_room(self, room_name: str) -> None:
        await self._perform_action(
            {"action": "create_room", "data": {"name": room_name}}
        )

    async def send_message(self, message: str) -> None:
        await self._perform_action(
            {"action": "send_message", "data": {"message": message}}
        )

    async def invite_user(self, user_id: str) -> None:
        await self._perform_action(
            {"action": "invite_user", "data": {"userId": user_id}}
        )

    async def accept_invite(self) -> None:
        await self._perform_action({"action": "accept_invite", "data": {}})

    async def reload(self) -> None:
        await self._perform_action({"action": "reload", "data": {}})

    async def clear_idb_storage(self) -> None:
        await self._perform_action({"action": "clear_idb_storage", "data": {}})

    async def change_room_history_visibility(self, history_visibility: str) -> None:
        await self._perform_action(
            {
                "action": "change_room_history_visibility",
                "data": {"historyVisibility": history_visibility},
            }
        )

    async def verify_message_in_timeline(self, message: str) -> None:
        await self._perform_action(
            {"action": "verify_message_in_timeline", "data": {"message": message}}
        )
