import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class VerifyClientTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice_one")
        self._client_under_test([ElementWeb()], "alice_two")
        self._server_under_test(Synapse(), ["server"])

    async def run(self, alice_one: MatrixClient, alice_two: MatrixClient, server: HomeServer) -> None:
        await alice_one.register(server)
        alice_two.localpart = alice_one.localpart
        alice_two.password = alice_one.password
        await alice_two.login(server)
        await alice_two.start_crosssign()
        await alice_one.accept_crosssign()
        await asyncio.gather(alice_one.accept_crosssign(), alice_two.accept_crosssign())
