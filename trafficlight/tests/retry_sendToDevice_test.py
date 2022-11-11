import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class RetrySendToDeviceTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._server_under_test(Synapse(), ["server"])
        self._network_proxy("proxy")

    async def run(
            self, alice: MatrixClient, bob: MatrixClient, server: HomeServer, network_proxy: NetworkProxyClient
    ) -> None:
        await network_proxy.proxy_to(server)
        await alice.register(network_proxy)

        await alice.create_room("little test room")
        await bob.register(server)
        await alice.invite_user("@" + bob.localpart + ":" + server.server_name)
        await bob.accept_invite()
        await network_proxy.disable_endpoint("/_matrix/client/r0/sendToDevice")
        await alice.send_message("A random message appears!")
        await network_proxy.wait_until_endpoint_accessed(
            "/_matrix/client/r0/sendToDevice"
        )
        await bob.verify_last_message_is_utd()
        await network_proxy.enable_endpoint("/_matrix/client/r0/sendToDevice")
        await network_proxy.wait_until_endpoint_accessed(
            "/_matrix/client/r0/sendToDevice"
        )
        await asyncio.sleep(5000)
        await bob.verify_message_in_timeline("A random message appears!")
