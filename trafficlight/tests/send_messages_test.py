from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class SendMessagesTest(Test):
    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "client_one")
        self._server_under_test(Synapse(), "server")

    async def run(self, client_one: Client, server: HomeServer) -> None:

        await client_one.register(server)
        await client_one.create_room("little test room")
        await client_one.send_message("hi there!")