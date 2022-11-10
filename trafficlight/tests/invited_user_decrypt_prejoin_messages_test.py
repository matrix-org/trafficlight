import asyncio

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

class InviteUserDecryptPrejoinMessagesTestSuite(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test("alice", [ElementWeb(), ElementAndroid()])
        self._client_under_test("bob", [ElementWeb(), ElementAndroid()])
        self._server_under_test("server", Synapse())

    async def run(self, alice: Client, bob: Client, server: HomeServer) -> None:
        await alice.register(server)
        await alice.create_room("little test room")
        await alice.change_room_history_visibility("invited")
        await alice.send_message("Bob should not be able to read this as he isn't invited yet")
        await bob.register(server)
        await alice.invite_user("@"+bob.localpart+":"+server.server_name)
        await alice.send_message("Bob should be able to read this as he has been invited")
        await bob.accept_invite()
        await bob.verify_message_in_timeline("Bob should be able to read this as he has been invited")