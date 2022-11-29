from nio import AsyncClient

from trafficlight.client_types import HydrogenWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse

# Test Script:
# CLIENT_COUNT=0 REQUIRES_HYDROGEN=true HYDROGEN_APP_URL="http://localhost:3000" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server


class HydrogenActionsTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([HydrogenWeb()], "alice")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self,
        alice: MatrixClient,
        server: HomeServer,
    ) -> None:
        nio_client = AsyncClient(
            server.cs_api, f"@{alice.localpart}:{server.server_name}"
        )
        try:
            await nio_client.register(alice.localpart, alice.password)
            await alice.login(server)
            await alice.create_room("Test Room 1")
            await alice.send_message("Hello world!")
            await alice.create_room("Test Room 2")
            await alice.open_room("Test Room 1")
            await alice.reload()
            await alice.verify_message_in_timeline("Hello world!")
            await alice.logout()
            await alice.login(server)
            await alice.open_room("Test Room 1")
            await alice.verify_last_message_is_utd()
            await alice.clear_idb_storage()
        finally:
            await nio_client.close()
