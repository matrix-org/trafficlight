import asyncio

from trafficlight.client_types import ElementCall
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import ElementCallClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


import asyncio
from time import datetime

class VerifyClientTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")
        self._server_under_test(SynapseDevelop(), ["server"])

    async def run(
        self, alice: ElementCallClient, bob: ElementCallClient, server: HomeServer
    ) -> None:
	roomName = "tl_chat_"+datetime.now().timestamp()
        (alice_joined, bob_joined) = asyncio.gather(alice.create_or_join(), bob.create_or_join())

        # Check only one of alice or bob joined the room (the other created it)
        # between two single-bit booleans, this is xor
        assert alice_joined ^ bob_joined
        asyncio.gather(alice.lobby_join(), bob.lobby_join())
        (alice_data, bob_data) = await asyncio.gather(alice.get_call_data(), bob.get_call_data())

 
