from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class MessageDecryptionAfterStorageClearedTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "alice")
        self._client_under_test([ElementWeb(), ElementAndroid()], "bob")
        self._server_under_test(Synapse(), ["server"])

    async def run(self, alice: Client, bob: Client, server: HomeServer):
        await alice.register(server)
        await bob.register(server)
        await alice.create_room("little test room")
        await alice.invite_user("@"+bob.localpart+":"+server.server_name)
        await bob.accept_invite()
        await alice.clear_idb_storage()
        await alice.reload()
        await bob.send_message("Alice should be able to see this message")
        await alice.verify_message_in_timeline("Alice should be able to read this message")