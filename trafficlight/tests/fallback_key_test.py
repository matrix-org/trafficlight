import asyncio
import logging

from nio import AsyncClient, AsyncClientConfig, SyncResponse, store

from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


# CLIENT_COUNT=2  REQUIRES_PROXY=true CYPRESS_BASE_URL="https://app.element.io" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server
# Passing Test
class FallbackKeyTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice")
        self._client_under_test([ElementWebStable()], "bob")
        self._network_proxy("alice_proxy")
        self._server_under_test(SynapseDevelop(), ["server"])

    async def run(
        self,
        alice: MatrixClient,
        bob: MatrixClient,
        server: HomeServer,
        alice_proxy: NetworkProxyClient,
    ) -> None:
        await alice_proxy.proxy_to(server)
        await asyncio.gather(alice.register(alice_proxy), bob.register(server))
        room_id = await alice.create_room("fallback test room")
        logging.info(f"Got room-id as {room_id}")
        await alice.invite_user(f"{bob.localpart}:{server.server_name}")
        await bob.accept_invite()
        # disable sync for alice, so she can't upload more device keys
        await alice_proxy.disable_endpoint("/_matrix/client/r0/sync")
        for i in range(60):
            await login_and_send_message_in_room(
                server, bob, room_id, f"Hello world {i + 1}!"
            )
        await alice_proxy.enable_endpoint("/_matrix/client/r0/sync")
        # last message would have exhausted the OTKs,
        # so we should have fallen back to the fallback key
        await alice.verify_message_in_timeline("Hello world 60!")


async def login_and_send_message_in_room(
    server: HomeServer, user: MatrixClient, room_id: str, message: str
) -> None:
    # need to install python-olm and pip install "matrix-nio[e2e]
    logging.info(
        f"trying to login as @{user.localpart}:{server.server_name} with password ${user.password} and send a message in #{room_id}..."
    )
    user_id = f"@{user.localpart}:{server.server_name}"
    client = AsyncClient(
        server.cs_api,
        user_id,
        config=AsyncClientConfig(
            encryption_enabled=True, store=store.SqliteMemoryStore
        ),
    )

    # This method will be called after each sync
    async def handle_sync(_) -> None:
        # Send the message after initial sync
        await client.room_send(
            room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
            ignore_unverified_devices=True,
        )
        # Stop syncing
        task.cancel()

    try:
        client.add_response_callback(handle_sync, SyncResponse)
        await client.login(user.password)
        # sync_forever must be used for encryption to work
        task = asyncio.create_task(client.sync_forever(timeout=30000))
        await task
    except Exception as e:
        logging.exception(str(e))
    finally:
        await client.close()
