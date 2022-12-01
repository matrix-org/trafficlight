import asyncio

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseStable


class InviteUserDecryptPrejoinMessagesTestSuite(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._client_under_test([ElementWebStable()], "bob")
        self._server_under_test(SynapseStable(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await asyncio.gather(alice.register(server), bob.register(server))
        await alice.create_room("little test room")
        await alice.change_room_history_visibility("invited")
        await alice.send_message(
            "Bob should not be able to read this as he isn't invited yet"
        )

        await alice.invite_user(bob.localpart + ":" + server.server_name)
        await alice.send_message(
            "Bob should be able to read this as he has been invited"
        )
        await bob.accept_invite()
        await bob.verify_message_in_timeline(
            "Bob should be able to read this as he has been invited"
        )
