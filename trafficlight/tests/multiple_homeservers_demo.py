from trafficlight.client_types import ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import MixedFederation


class SendMessagesAcrossFederationTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb()], "client_one")
        self._client_under_test([ElementWeb()], "client_two")
        self._server_under_test(MixedFederation(), ["server", "second_server"])

    async def run(
        self,
        client_one: Client,
        client_two: Client,
        server: HomeServer,
        second_server: HomeServer,
    ) -> None:

        await client_one.register(server)
        await client_one.create_room("little test room")
        await client_one.send_message("hi there!")
        await client_two.register(second_server)
        await client_one.invite_user(
            "@" + client_two.localpart + ":" + second_server.server_name
        )
        await client_two.accept_invite()
        await client_two.verify_message_in_timeline("hi there!")
