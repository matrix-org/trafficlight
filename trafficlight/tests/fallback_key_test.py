import asyncio

from nio import AsyncClient
from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class FallbackKeyTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")
        self._network_proxy("alice_proxy")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer, alice_proxy: NetworkProxyClient
    ) -> None:
        await alice_proxy.proxy_to(server)
        await asyncio.gather(
            alice.register(alice_proxy), bob.register(server)
        )
        await alice.create_room("fallback test room")
        await alice.invite_user(f"{bob.localpart}:{server.server_name}")
        await bob.accept_invite()
        # disable sync for alice, so she can't upload more device keys
        await alice_proxy.disable_endpoint("/_matrix/client/r0/sync")

        # for 1...60
        bob_client_n = AsyncClient(
            server.cs_api, f"@{bob.localpart}:{server.server_name}"
        )
        login_resp = await bob_client_n.login(bob.password)

        # check that we logged in succesfully
        if isinstance(login_resp, LoginResponse):
            
        else:
            print(f'homeserver = "{homeserver}"; user = "{user_id}"')
            print(f"Failed to log in: {login_resp}")
            sys.exit(1)

        await alice_proxy.enable_endpoint("/_matrix/client/r0/sync")
