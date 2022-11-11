from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class LargePollTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "alice")
        self._client_under_test([ElementWeb(), ElementAndroid()], "bob")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self, alice: MatrixClient, bob: MatrixClient, server: HomeServer
    ) -> None:
        await alice.register(server)
        await alice.create_room("little test room")
        await bob.register(server)
        await alice.invite_user("@" + bob.localpart + ":" + server.server_name)
        await bob.accept_invite()
        # await alice.create_poll("Options go here!", ["a", "b", "c"])

        # TODO implement this. In the server-side part of the test is fine
        # But make it asyncio-based so it doesn't block the rest of the server's logic.
        # await generate_fake_users_and_respond_to_poll(1000)
        # poll_responses = await alice.verify_poll("Options go here!")
        # assertEquals(len(poll_responses) == 1000)
