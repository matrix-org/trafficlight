import asyncio
from datetime import datetime

from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage
from trafficlight.internals.test import Test


class ElementCallTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        room_name = "tl_chat_" + str(datetime.now().timestamp())
        await alice.create(room_name)
        alice_lobby = await alice.get_lobby_data()

        await bob.join_by_url(alice_lobby.invite_url)

        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        # Check that both alice and bob are captioned in the video streams of both users
        print(alice_data)
        print(bob_data)

        # Fricking TODO: get a matcher library in here somehow.
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

        bob_data = await bob.get_call_data()

        assert len(bob_data.video_tiles) == 2

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert alice_tile.video_image_colour() == VideoImage.BLUE
