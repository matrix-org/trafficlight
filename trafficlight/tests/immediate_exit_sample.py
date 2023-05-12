import asyncio

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


class ExitImmediately(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._server_under_test(SynapseDevelop(), ["server"])
        self._network_proxy("network_proxy")

    async def run(
        self,
        alice: MatrixClient,
        server: HomeServer,
        network_proxy: NetworkProxyClient,
    ) -> None:
        # All we do is exit the client immediately
        # Used for manual testing that clients will restart correctly
        # on immediate exit.
        await network_proxy.proxy_to(server)
        await asyncio.sleep(5)
