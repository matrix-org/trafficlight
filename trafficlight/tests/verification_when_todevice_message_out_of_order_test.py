import asyncio

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop

# Test Script:
# CLIENT_COUNT=2 REQUIRES_PROXY=true CYPRESS_BASE_URL="https://develop.element.io" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server

# Test Status: Passing


class VerifyWhenToDeviceMessagesOutOfOrder(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice_one")
        self._client_under_test([ElementWebStable()], "alice_two")
        self._server_under_test(SynapseDevelop(), ["server"])
        self._network_proxy("network_proxy")

    async def run(
        self,
        alice_one: MatrixClient,
        alice_two: MatrixClient,
        server: HomeServer,
        network_proxy: NetworkProxyClient,
    ) -> None:
        await network_proxy.proxy_to(server)
        alice_two.localpart = alice_one.localpart
        alice_two.password = alice_one.password
        await alice_one.register(network_proxy)
        await alice_two.login(network_proxy)
        await network_proxy.delay_endpoint(
            "/_matrix/client/r0/sendToDevice/m.key.verification.ready", 30000
        )
        await alice_two.start_crosssign()
        await alice_one.accept_crosssign()
        await asyncio.sleep(30)
        await asyncio.gather(alice_one.verify_crosssign(), alice_two.verify_crosssign())
