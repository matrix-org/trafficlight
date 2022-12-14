import asyncio

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


class MessageDecryptionWhenOwnHSOfflineTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._client_under_test([ElementWebStable()], "bob_one")
        self._client_under_test([ElementWebStable()], "bob_two")
        self._network_proxy("network_proxy")
        self._server_under_test(SynapseDevelop(), ["server"])

    async def run(
        self,
        alice: MatrixClient,
        bob_one: MatrixClient,
        bob_two: MatrixClient,
        network_proxy: NetworkProxyClient,
        server: HomeServer,
    ) -> None:
        # Overwrite generated password in bob_two with bob_one
        bob_two.password = bob_one.password
        bob_two.localpart = bob_one.localpart

        await network_proxy.proxy_to(server)

        await alice.register(network_proxy)

        await bob_one.register(server)
        await alice.create_room("little test room")
        await alice.invite_user(f"{bob_one.localpart}:{server.server_name}")
        await bob_one.accept_invite()
        await network_proxy.disable_endpoint("/_matrix/client/r0/sync")
        await bob_two.login(server)
        await bob_two.open_room("little test room")
        await alice.send_message("A random message appears!")
        await network_proxy.enable_endpoint("/_matrix/client/r0/sync")
        await asyncio.sleep(5000)
        await asyncio.gather(
            bob_one.verify_message_in_timeline("A random message appears!"),
            bob_two.verify_message_in_timeline("A random message appears!"),
        )
