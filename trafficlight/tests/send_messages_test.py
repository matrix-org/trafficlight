import logging

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

from nio import AsyncClient, MatrixRoom, RoomMessageText

logger = logging.getLogger(__name__)

class SendMessagesTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "client_one")
        self._server_under_test(Synapse(), ["server"])

    async def run(self, client_one: MatrixClient, server: HomeServer) -> None:
        await client_one.register(server)
        await client_one.create_room("little test room")
        await client_one.send_message("hi there!")
        logger.info("Investigating rooms directly")
        client = AsyncClient(server.cs_api, f"@{client_one.localpart}:{server.server_name}")
        await client.login(client_one.password)
        logger.info(f"{client.rooms}")



