import asyncio

from trafficlight.client_types import ElementCall
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import ElementCallClient
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


import asyncio
from datetime import datetime

class VerifyClientTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")
        self._server_under_test(SynapseDevelop(), names=["server"])

    async def run(
        self, alice: ElementCallClient, bob: ElementCallClient, server: HomeServer
    ) -> None:
        roomName = "tl_chat_"+str(datetime.now().timestamp())
        (alice_joined, bob_joined) = await asyncio.gather(alice.create_or_join(roomName, "alice"), bob.create_or_join(roomName, "bob"))

        # Check only one of alice or bob joined the room (the other created it)
        # between two single-bit booleans, this is xor
        print(str(alice_joined) + " or "+ str(bob_joined))

        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)
        (alice_data, bob_data) = await asyncio.gather(alice.get_call_data(), bob.get_call_data())

        # Check that both alice and bob are captioned in the video streams of both users
        alice_data = alice_data['videos']
        bob_data = bob_data['videos']
        print (alice_data)
        print (bob_data)
        assert any(map(lambda x: x["caption"] == "alice", alice_data))
        assert any(map(lambda x: x["caption"] == "bob", alice_data))
        assert any(map(lambda x: x["caption"] == "alice", bob_data))
        assert any(map(lambda x: x["caption"] == "bob", bob_data))

        # No-one was muted, so assert no-one has been muted.
        assert not any(map(lambda x: x["muted"], alice_data))
        assert not any(map(lambda x: x["muted"], bob_data))
 
