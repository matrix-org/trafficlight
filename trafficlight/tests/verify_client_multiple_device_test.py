import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class VerifyClientMultipleDeviceTestSuite(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await asyncio.gather(alice.register(server), bob.register(server))
        await alice.create_dm(f"{bob.localpart}:{server.server_name}")
        await alice.send_message("Send a message to ensure DM is created")
        await bob.accept_invite()
        await bob.start_crosssign(f"{alice.localpart}:{server.server_name}")
        await alice.accept_crosssign()
        await asyncio.gather(alice.verify_crosssign(), bob.verify_crosssign())
