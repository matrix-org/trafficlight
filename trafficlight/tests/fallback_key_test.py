import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class FallbackKeyTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await asyncio.gather(
            alice.register(server), bob.register(second_server)
        )
        await alice.create_room("fallback test room")
        await alice.invite_user(
            bob.localpart + ":" + second_server.server_name
        )
        await bob.accept_invite()
        await alice.go_offline()
