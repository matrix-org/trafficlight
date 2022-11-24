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
        # TODO: does alice need to enable fallback keys? 
        room_id = await alice.create_room("fallback test room")
        await alice.invite_user(f"{bob.localpart}:{server.server_name}")
        await bob.accept_invite()
        # disable sync for alice, so she can't upload more device keys
        await alice_proxy.disable_endpoint("/_matrix/client/r0/sync")
        for i in range(1, 61):
            await login_and_send_message_in_room(server, bob, room_id, f"Hello world {i}!")
        await alice_proxy.enable_endpoint("/_matrix/client/r0/sync")
        # last message would have exhausted the OTKs,
        # so we should have fallen back to the fallback key
        await alice.verify_message_in_timeline("Hello world 60!")

async def login_and_send_message_in_room(server: HomeServer, user: MatrixClient, room_id: str, message: str) -> None:
    # TODO: will this encrypt (and hence track the room and claim keys)??
    # need to install python-olm and pip install "matrix-nio[e2e]
    client = AsyncClient(
        server.cs_api, f"@{user.localpart}:{server.server_name}"
    )
    try:
        await client.login(user.password)
        await client.room_send(
            room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )
    finally:
        await client.close()
