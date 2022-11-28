import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import TwoSynapseFederation


class SendMessagesAcrossFederationTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._server_under_test(TwoSynapseFederation(), ["alice_server", "bob_server"])

    async def run(
        self,
        alice: MatrixClient,
        bob: MatrixClient,
        alice_server: HomeServer,
        bob_server: HomeServer,
    ) -> None:

        await asyncio.gather(alice.register(alice_server), bob.register(bob_server))
        await alice.create_room("little test room")
        await alice.send_message("hi there!")
        await alice.invite_user(bob.localpart + ":" + bob_server.server_name)
        await bob.accept_invite()
        await bob.verify_message_in_timeline("hi there!")
        await bob.send_message("Thanks for inviting me alice")
        await alice.verify_message_in_timeline("Thanks for inviting me alice")
