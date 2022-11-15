import logging

from nio import AsyncClient

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

logger = logging.getLogger(__name__)


class SendMessagesTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "client_one")
        self._server_under_test(Synapse(), ["server"])

    async def run(self, client_one: MatrixClient, server: HomeServer) -> None:
        await client_one.register(server)
        await client_one.create_room("little test room")
        await client_one.send_message("hi there!")

        # Not sure if we'd actually want to do this as it stands, and the test isn't that useful
        # but it demonstrates use of out of band client usage and asserts

        # Once we actually use this in anger, I'd suggest we do some refactoring and provide some utilities
        # or possibly even make something pre-made and available in the run method parameters.

        # Problem for the person writing that test.

        nio_client = AsyncClient(
            server.cs_api, f"@{client_one.localpart}:{server.server_name}"
        )
        try:
            logger.info("Investigating rooms directly")
            await nio_client.login(client_one.password)
            await nio_client.sync()

            room = list(nio_client.rooms.values())[0]
            assert room.name == "little test room"

        finally:
            await nio_client.close()
