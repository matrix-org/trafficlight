import asyncio
import logging
import random
import string
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, Optional, Union, List, Tuple

from PIL import Image  # type: ignore
from nio import AsyncClient

from trafficlight.homerunner import HomeServer
from trafficlight.internals.exceptions import ActionException

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


class VideoImage(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass
class VideoTile:
    caption: str
    muted: bool
    screenshare: bool
    snapshot_file: str

    def video_image_is(self, colour: VideoImage) -> bool:
        with Image.open(self.snapshot_file) as im:
            width = im.width
            height = im.height
            pixel: Tuple[int,int,int,int] = im.getpixel((int(width / 2), int(height / 2))) #
            # Pixel is R,G,B,A tuple (A = alpha)
            match colour:
                case VideoImage.RED:
                    return pixel == (255, 0, 0, 0)
                case VideoImage.GREEN:
                    return pixel == (0, 255, 0, 0)
                case VideoImage.BLUE:
                    return pixel == (0, 0, 255, 0)

            return False


@dataclass
class LobbyData:
    video_muted: bool
    muted: bool
    snapshot_file: str
    page_url: str
    invite_url: str
    call_name: str


@dataclass
class CallData:
    video_tiles: List[VideoTile]
    muted: bool
    screenshare: bool
    video_muted: bool
    page_url: str
    invite_url: str
    call_name: str

    def get_video_tile_by_caption(self, caption: str) -> VideoTile:
        tiles = list(filter(lambda x: x.caption == caption, self.video_tiles))
        if len(tiles) != 1:
            logger.info(f"Found tiles {tiles} out of {self.video_tiles}")
            raise AssertionError(f"found {len(tiles)} videos with caption {caption}")
        else:
            return tiles[0]


class ElementCallClient(Client):
    _NO_USER = "no_user"
    _REGISTERED_USER = "registered_user"
    _GUEST_USER = "guest_user"

    def __init__(self, name: str, test_case: Any, registration: Dict[str, Any]):
        super().__init__(name, test_case, registration)
        self.type = self._NO_USER
        self.localpart: Optional[str] = None
        self.password: Optional[str] = None
        self.display_name: Optional[str] = None
        # This letter is used to prefix matrix IDs.
        self._random_letter: str = random.choice(string.ascii_lowercase)

    async def login(self, localpart: str, password: str) -> None:
        self.type = self._REGISTERED_USER
        self.localpart = localpart
        self.password = password
        await self._perform_action(
            {"action": "login", "data": {"localpart": self.localpart, "password": self.password}}
        )

    async def login_as(self, other_client: "ElementCallClient") -> None:
        await self.login(other_client.localpart, other_client.password)

    async def register(self) -> None:
        self.type = self._REGISTERED_USER
        self.localpart = "user_" + self._random_letter + "_" + self.name + "_" + str(round(time.time()))
        self.password = "pass_bibble_bobble_" + self.name

        await self._perform_action(
            {"action": "register", "data": {"localpart": self.localpart, "password": self.password}}
        )

    async def guest_user(self) -> None:
        self.type = self._GUEST_USER
        self.display_name = self.name

    async def set_display_name(self) -> None:
        self.display_name = self.name
        await self._perform_action(
            {"action": "set_display_name", "data": {"display_name": self.display_name}}
        )

    async def logout(self) -> None:
        await self._perform_action(
            {"action": "logout", "data": {}}
        )

    async def recreate(self, unload_hooks: bool = False) -> None:
        await self._perform_action({"action": "recreate", "data": {"unload_hooks": unload_hooks}})

    async def reload(self) -> None:
        await self._perform_action({"action": "reload", "data": {}})

    async def create_or_join(self, call_name: str) -> bool:
        if self.type == self._GUEST_USER:
            data = await self._perform_action(
                {"action": "create_or_join", "data": {"call_name": call_name, "display_name": self.display_name}})
        elif self.type == self._REGISTERED_USER:
            data = await self._perform_action(
                {"action": "create_or_join", "data": {"call_name": call_name}})
        else:
            raise ActionException("User unspecified; login(), register() or guest_user() first", "client.py")

        if "existing" in data:
            return "true" == data["existing"]  # type: ignore
        else:
            return False

    async def join_by_url(self, call_url: str) -> None:
        if self.type == self._GUEST_USER:
            await self._perform_action(
                {"action": "join_by_url", "data": {"call_url": call_url, "display_name": self.display_name}})
        elif self.type == self._REGISTERED_USER:
            await self._perform_action({"action": "join_by_url", "data": {"call_url": call_url}})
        else:
            raise ActionException("User unspecified; login(), register() or guest_user() first", "client.py")

    async def get_lobby_data(self) -> LobbyData:
        response = await self._perform_action({"action": "get_lobby_data", "data": {}})

        data = response['data']
        snapshot_file = self.test_case.files[self.name + "_" + data['snapshot']]
        invite_url = response['data']['invite_url']
        page_url = response['data']['page_url']
        call_name = response['data']['call_name']
        lobby_data = LobbyData(video_muted=False, muted=False, snapshot_file=snapshot_file, page_url=page_url,
                               invite_url=invite_url, call_name=call_name)
        return lobby_data

    async def lobby_join(self) -> None:
        await self._perform_action({"action": "lobby_join", "data": {}})

    async def get_call_data(self) -> CallData:
        response = await self._perform_action({"action": "get_call_data", "data": {}})

        # TODO marshall properly, because this is rubbish.
        print(response)
        videos = response['data']['videos']
        tiles: List[VideoTile] = []
        for video in videos:
            # convert from adapter naming to our naming.
            snapshot_file = self.test_case.files[self.name + "_" + video['snapshot']]
            tiles.append(VideoTile(caption=video['caption'], muted=video['muted'], screenshare=False,
                                   snapshot_file=snapshot_file))

        invite_url = response['data']['invite_url']
        page_url = response['data']['page_url']
        call_name = response['data']['call_name']
        call_data = CallData(screenshare=False, video_muted=False, muted=False, video_tiles=tiles, page_url=page_url,
                             invite_url=invite_url, call_name=call_name)

        return call_data

    async def set_video_image(self, image: VideoImage) -> None:
        await self._perform_action({"action": "set_video_image", "data": {"image": str(image)}})

    async def set_mute(self, audio_mute: bool, video_mute: bool) -> None:
        await self._perform_action(
            {"action": "set_mute", "data": {"audio_mute": audio_mute, "video_mute": video_mute}})

    async def set_screenshare(self, screenshare: bool) -> None:
        await self._perform_action({"action": "set_screenshare", "data": {"screenshare": screenshare}})


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

        if (
                self.registration["type"] == "element-android"
                or self.registration["type"] == "element-ios"
        ):
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

    async def _direct_registration(
            self, homeserver: Union[HomeServer, NetworkProxyClient]
    ) -> None:
        nio_client = AsyncClient(homeserver.cs_api)
        response = await nio_client.register(
            self.localpart, self.password, device_name="TLRegisterHack"
        )
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
