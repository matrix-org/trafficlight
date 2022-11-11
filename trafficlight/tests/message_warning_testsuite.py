from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class MessageWarningTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._server_under_test(Synapse(), ["server"])

    async def run(self, alice: Client, bob: Client, server: HomeServer) -> None:
        await alice.register(server)
        await bob.register(server)
        await bob.enable_key_backup("helloworld123helloworld")
        await alice.create_room("little test room")
        await alice.invite_user(f'@{bob.localpart}:{server.server_name}')
        await bob.accept_invite()
        await alice.send_message("Bob should be able to read this message!")
        await bob.logout()
        await bob.login(server, "helloworld123helloworld")
        await bob.enter_room("little test room")
        await bob.verify_message_in_timeline("Bob should be able to read this message!")
        await bob.verify_last_message_is_trusted()