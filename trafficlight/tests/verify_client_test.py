import asyncio

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class VerifyClientTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "alice")
        self._client_under_test([ElementWeb(), ElementAndroid()], "bob")
        self._server_under_test(Synapse(), "server")

    async def run(self, alice: Client, bob: Client, server: HomeServer) -> None:

        await alice.register(server)
        # Ensure bob logs in as same user as alice
        bob.localpart = alice.localpart
        bob.password = alice.password
        await bob.login(server)
        await bob.start_crosssign()
        await alice.accept_crosssign()
        await asyncio.gather(alice.accept_crosssign(), bob.accept_crosssign())
