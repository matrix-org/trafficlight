import asyncio
from typing import cast

from trafficlight.client_types import ElementCall
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import ElementCallClient, VideoImage, CallData
from trafficlight.internals.test import Test
from trafficlight.server_types import SynapseDevelop


import asyncio
from datetime import datetime

class ElementCallTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(
        self, alice: ElementCallClient, bob: ElementCallClient
    ) -> None:
        room_name = "tl_chat_"+str(datetime.now().timestamp())
        (alice_joined, bob_joined) = await asyncio.gather(alice.create_or_join(room_name, "alice"), bob.create_or_join(room_name, "bob"))

        # Check only one of alice or bob joined the room (the other created it)
        # between two single-bit booleans, this is xor
        print(str(alice_joined) + " or " + str(bob_joined))

        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        # Check that both alice and bob are captioned in the video streams of both users
        print (alice_data)
        print (bob_data)

        ## Fricking TODO: get a matcher library in here somehow.
        assert any(map(lambda x: x.caption == "alice", alice_data.video_tiles))
        assert any(map(lambda x: x.caption == "bob", alice_data.video_tiles))
        assert any(map(lambda x: x.caption == "alice", bob_data.video_tiles))
        assert any(map(lambda x: x.caption == "bob", bob_data.video_tiles))

        # No-one was muted, so assert no-one has been muted.
        assert not any(map(lambda x: x.muted, alice_data.video_tiles))
        assert not any(map(lambda x: x.muted, bob_data.video_tiles))

        assert not alice_data.muted
        assert not alice_data.video_muted
        assert not alice_data.screenshare

        await alice.set_video_image(VideoImage.BLUE)
        await alice.set_mute(True, False)
        await alice.set_screenshare(True)
 
        bob_data = await bob.get_call_data()
        alice_from_bob = list(filter(lambda x: x.caption == "alice", bob_data.video_tiles))[0]
        assert alice_from_bob.caption == "alice"
        assert alice_from_bob.muted
        # assert alice_screenshare_from_bob.snapshot_file compared_to blue_image

        # Find the screenshare somehow and then match...
        # alice_screenshare_from_bob = list(filter(lambda x: x.caption == "alice_screenshare", bob_data.video_tiles))[0]

        # assert alice_screenshare_from_bob.snapshot_file compared_to alice_screenshare_image == True
