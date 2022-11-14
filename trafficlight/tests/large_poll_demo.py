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

        # This would need implementation in the client adapters
        # and a small method made to marshal the method call into
        # some appropriate call.

        # await alice.create_poll("Options go here!", ["a", "b", "c"])
        # For example, instantiate a matrix-nio client and register
        # join the room, then find the most recent poll and respond to it appropriately.
        # await that completing
        # await generate_fake_users_and_respond_to_poll(1000)

        # verify_poll should inspect the information in the app and
        # return something here like {"a": 333, "b": 333", c:"334"}
        # in the response from the action
        # poll_responses = await alice.verify_poll("Options go here!")
        # Do an assertion on the poll responses.
