import logging

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

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
        timeline = await client_one.get_timeline()
        logger.info(timeline)
        # TODO: work out what to do about that first timeline element
        # Which is actually a box because it's not real in the timeline...
        assert timeline[1].get("message") == "hi there!"
        assert (
            timeline[1].get("user") == f"@{client_one.localpart}:{server.server_name}"
        )
