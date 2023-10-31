import asyncio
from datetime import datetime

from assertpy import assert_that  # type: ignore

from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage
from trafficlight.internals.test import Test

# Tests


class JoinCallReceiveVideoTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        await asyncio.gather(alice.register(), bob.register())

        await asyncio.gather(alice.set_display_name(), bob.set_display_name())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        await alice.create(room_name)
        alice_lobby = await alice.get_lobby_data()

        await bob.join_by_url(alice_lobby.invite_url)
        # lobby screen
        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        await asyncio.gather(
            alice.set_video_image(VideoImage.BLUE), bob.set_video_image(VideoImage.RED)
        )

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        assert len(alice_data.video_tiles) == 2
        assert len(bob_data.video_tiles) == 2

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert_that(bob_tile.video_image_colour()).is_equal_to(VideoImage.RED)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert_that(alice_tile.video_image_colour()).is_equal_to(VideoImage.BLUE)

        await alice.set_video_image(VideoImage.GREEN)
        await asyncio.sleep(2)
        bob_data = await bob.get_call_data()

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert_that(alice_tile.video_image_colour()).is_equal_to(VideoImage.GREEN)
