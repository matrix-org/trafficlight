import logging

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

logger = logging.getLogger(__name__)


class AlternativeTestExample(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "alice")
        self._client_under_test([ElementWeb(), ElementAndroid()], "bob")
        # Nearly there ..
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        """
        Run: called after an adapter is found for each client and a homeserver instance has been created.
        @return:
        """
        logger.info(f"{alice} {bob}, {server}")
        await alice.register(server)
        await bob.register(server)

        await alice.create_room("Poll Test Room")
