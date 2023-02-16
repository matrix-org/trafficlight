import asyncio
import logging
from typing import Any, Dict, Optional, Union
import time
from nio import AsyncClient

from trafficlight.homerunner import HomeServer

logger = logging.getLogger(__name__)

DEFAULT_POLL_RESPONSE: Dict[str, Any] = {
    "action": "idle",
    "data": {"delay": 5000, "reason": "waiting for action from test case"},
}


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id


class Client:
    def __init__(
        self,
        name: str,
        test_case: Any,
        registration: Dict[str, Any],
    ):
        self.name = name
        self.test_case = test_case
        self.registration = registration

        self.current_poll_response = DEFAULT_POLL_RESPONSE
        self.current_poll_future: Optional[asyncio.Future[Dict[str, Any]]] = None

        # Store an exception if if comes in while we're not awaiting something
        self.next_exception: Exception = None

    def __repr__(self) -> str:
        return self.name

    # Called by the http client API
    def _get_poll_data(self) -> Dict[str, Any]:
        return self.current_poll_response

    # Called by the http client API
    def _give_poll_response(self, data: Dict[str, Any]) -> None:
        if self.current_poll_future is not None:
            self.current_poll_future.set_result(data)
        else:
            raise Exception("Unable to handle response; not awaiting that.")

        # resolve the promise s.t. register returns

    def _give_poll_exception(self, exception: Exception) -> None:
        if self.current_poll_future is not None:
            self.current_poll_future.set_exception(exception)
        else:
            # Store exception for next time we perform an action.
            self.next_exception = exception

    # used by named methods from the test
    async def _perform_action(self, question: Dict[str, Any]) -> Dict[str, Any]:
        if self.current_poll_future is not None:
            raise Exception(
                "Action collision: already waiting for response to "
                + str(self.current_poll_response)
            )

        if self.next_exception is not None:
            exception = self.next_exception
            self.next_exception = None
            raise exception

        self.current_poll_response = question
        self.current_poll_future = asyncio.get_running_loop().create_future()

        try:
            rsp = await self.current_poll_future
        finally:
            self.current_poll_future = None
            self.current_poll_response = DEFAULT_POLL_RESPONSE

        return rsp


class NetworkProxyClient(Client):
    def __init__(self, name: str, test_case: Any, registration: Dict[str, Any]):
        super().__init__(name, test_case, registration)
        self.server: Optional[HomeServer] = None
        # save the API endpoint
        self.cs_api = registration["endpoint"]
        self.server_name: Optional[str] = None

    async def proxy_to(self, server: HomeServer) -> None:
        self.server_name = server.server_name
        cs_api = server.cs_api
        await self._perform_action({"action": "proxyTo", "data": {"url": cs_api}})

    async def wait_until_endpoint_accessed(self, endpoint: str) -> None:
        await self._perform_action(
            {"action": "waitUntilEndpointAccessed", "data": {"endpoint": endpoint}}
        )

    async def enable_endpoint(self, endpoint: str) -> None:
        await self._perform_action(
            {"action": "enableEndpoint", "data": {"endpoint": endpoint}}
        )

    async def disable_endpoint(self, endpoint: str) -> None:
        await self._perform_action(
            {"action": "disableEndpoint", "data": {"endpoint": endpoint}}
        )

    async def delay_endpoint(self, endpoint: str, delay: int) -> None:
        await self._perform_action(
            {"action": "delayEndpoint", "data": {"endpoint": endpoint, "delay": delay}}
        )


class MatrixClient(Client):
    def __init__(self, name: str, test_case: Any, registration: Dict[str, Any]):
        super().__init__(name, test_case, registration)
        # Client login details
        self.localpart = "user_" + name + "_" + str(round(time.time()))
        self.password = "pass_bibble_bobble_" + name

    # exposed to the test to act
    async def register(self, homeserver: Union[HomeServer, NetworkProxyClient]) -> None:
        url = homeserver.cs_api
        docker_api = url.replace("localhost", "10.0.2.2")

        # Vicious Hack.
        # We're migrating away from "registration" in the client in favour of OIDC based
        # signup. This means we won't have the registration flow visible in EIX / EAX.

        # Rather than refactoring away from registration flows in element-web and others
        # we choose to emulate registration flow on the client by performing a registration
        # via API, removing that device and then passing those credentials as a login request.

        if self.registration['type'] == "element-android" or self.registration['type'] == "element-ios":
            # do nio based registration and logout
            await self._direct_registration(homeserver)
            # Then login with same credentials
            await self.login(homeserver, None)
            return

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


    async def _direct_registration(self, homeserver: Union[HomeServer, NetworkProxyClient]):
        nio_client = AsyncClient(homeserver.cs_api)
        response = await nio_client.register(self.localpart, self.password, device_name="TLRegisterHack")
        logger.info(response)
        response = await nio_client.logout()
        logger.info(response)

    async def login(
        self,
        homeserver: Union[HomeServer, NetworkProxyClient],
        key_backup_passphrase: str = None,
    ) -> None:
        url = homeserver.cs_api
        docker_api = url.replace("localhost", "10.0.2.2")

        data = {
            "username": self.localpart,
            "password": self.password,
            "homeserver_url": {"local_docker": docker_api, "local": url},
        }

        if key_backup_passphrase:
            data = {**data, "key_backup_passphrase": key_backup_passphrase}

        await self._perform_action({"action": "login", "data": data})


    async def start_crosssign(self, user_id: str = None) -> None:
        data: Dict[str, Any] = {}
        if user_id:
            data = {**data, "userId": user_id}

        await self._perform_action({"action": "start_crosssign", "data": data})

    async def accept_crosssign(self) -> None:
        await self._perform_action({"action": "accept_crosssign", "data": {}})

    async def verify_crosssign(self) -> None:
        await self._perform_action({"action": "verify_crosssign_emoji", "data": {}})

    async def create_room(self, room_name: str) -> None:
        await self._perform_action(
            {"action": "create_room", "data": {"name": room_name}}
        )

    async def create_dm(self, user_id: str) -> None:
        await self._perform_action({"action": "create_dm", "data": {"userId": user_id}})

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

    async def logout(self) -> None:
        await self._perform_action({"action": "logout", "data": {}})

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

    async def get_timeline(self) -> Any:
        response = await self._perform_action({"action": "get_timeline", "data": {}})
        return response["timeline"]

    async def verify_last_message_is_trusted(self) -> None:
        await self._perform_action(
            {"action": "verify_last_message_is_trusted", "data": {}}
        )

    async def verify_last_message_is_utd(self) -> None:
        await self._perform_action({"action": "verify_last_message_is_utd", "data": {}})

    async def verify_trusted_device(self) -> None:
        await self._perform_action({"action": "verify_trusted_device", "data": {}})

    async def enable_dehydrated_device(self, key_backup_passphrase: str) -> None:
        await self._perform_action(
            {
                "action": "enable_dehydrated_device",
                "data": {"key_backup_passphrase": key_backup_passphrase},
            }
        )

    async def enable_key_backup(self, key_backup_passphrase: str) -> None:
        await self._perform_action(
            {
                "action": "enable_key_backup",
                "data": {"key_backup_passphrase": key_backup_passphrase},
            }
        )

    async def open_room(self, room_name: str) -> None:
        await self._perform_action({"action": "open-room", "data": {"name": room_name}})

    async def advance_clock(self, duration: int) -> None:
        await self._perform_action(
            {"action": "advance_clock", "data": {"milliseconds": duration}}
        )
