from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseStable


class DehydratedDeviceTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._client_under_test([ElementWebStable()], "bob")
        self._server_under_test(SynapseStable(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await alice.register(server)
        await bob.register(server)
        await alice.enable_dehydrated_device("helloworld123helloworld")
        await bob.create_room("little test room")
        await bob.invite_user(f"@{alice.localpart}:{server.server_name}")
        await alice.accept_invite()
        await alice.logout()
        await bob.advance_clock(1209600000)
        await bob.send_message("Alice should be able to read this message!")
        await alice.login(server, key_backup_passphrase="helloworld123helloworld")
        await alice.open_room("little test room")
        await alice.verify_message_in_timeline(
            "Alice should be able to read this message!"
        )
