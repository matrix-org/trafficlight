import asyncio

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


class MessageWarningTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._client_under_test([ElementWebStable()], "bob")
        self._server_under_test(SynapseDevelop(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await asyncio.gather(alice.register(server), bob.register(server))
        await bob.enable_key_backup("helloworld123helloworld")
        await alice.create_room("little test room")
        await alice.invite_user(f"{bob.localpart}:{server.server_name}")
        await bob.accept_invite()
        await alice.send_message("Bob should be able to read this message!")
        await bob.logout()
        await bob.login(server, "helloworld123helloworld")
        await bob.open_room("little test room")
        await bob.verify_message_in_timeline("Bob should be able to read this message!")
        await bob.verify_last_message_is_trusted()
