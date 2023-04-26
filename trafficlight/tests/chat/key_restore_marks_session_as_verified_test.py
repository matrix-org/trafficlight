from trafficlight.client_types import ElementWebStable
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop

# Test Command:
# CLIENT_COUNT=2 CYPRESS_BASE_URL="https://develop.element.io"
# ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server


class KeyRestoreMarksSessionAsVerifiedTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWebStable()], "alice_one")
        self._client_under_test([ElementWebStable()], "alice_two")
        self._server_under_test(SynapseDevelop(), ["server"])

    async def run(
        self, alice_one: MatrixClient, alice_two: MatrixClient, server: HomeServer
    ) -> None:
        # Ensure alice_two logs in the same as alice_one.
        alice_two.localpart = alice_one.localpart
        alice_two.password = alice_one.password

        await alice_one.register(server)
        await alice_one.enable_key_backup("helloworld123helloworld")
        await alice_two.login(server, key_backup_passphrase="helloworld123helloworld")
        await alice_one.verify_trusted_device()
