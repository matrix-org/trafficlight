import asyncio

from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


# Test Script:
# CLIENT_COUNT=2 REQUIRES_PROXY=true CYPRESS_BASE_URL="https://develop.element.io"
# ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server

class VerifyWhenToDeviceMessagesOutOfOrder(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb()], "alice_one")
        self._client_under_test([ElementWeb()], "alice_two")
        self._server_under_test(Synapse(), ["server"])
        self._network_proxy("network_proxy")

    async def run(self, alice_one: MatrixClient, alice_two: MatrixClient, server: HomeServer,
                  network_proxy: NetworkProxyClient) -> None:
        await network_proxy.proxy_to(server)
        await alice_one.register(network_proxy)
        await alice_two.login(network_proxy)
        await network_proxy.delay_endpoint("/_matrix/client/r0/sendToDevice/m.key.verification.ready", 30000)
        await alice_two.start_crosssign()
        await alice_one.accept_crosssign()
        await asyncio.gather(alice_one.verify_crosssign(), alice_two.verify_crosssign())
