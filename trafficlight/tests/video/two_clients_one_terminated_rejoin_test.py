import asyncio
from datetime import datetime

from assertpy import assert_that  # type: ignore

from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage
from trafficlight.internals.test import Test

# Does not match any item in the spreadsheet


class TwoClientsOneTerminatedAndRejoin(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        await asyncio.gather(alice.register(), bob.register())

        await asyncio.gather(alice.set_display_name(), bob.set_display_name())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        await asyncio.gather(
            alice.create_or_join(room_name), bob.create_or_join(room_name)
        )

        await alice.set_video_image(VideoImage.BLUE)
        await bob.set_video_image(VideoImage.RED)

        # lobby screen
        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(3)

        alice_data = await alice.get_call_data()
        assert_that(alice_data.video_tiles).is_length(2)

        bob_data = await alice.get_call_data()
        assert_that(bob_data.video_tiles).is_length(2)

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert_that(bob_tile.video_image_colour()).is_equal_to(VideoImage.RED)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert_that(alice_tile.video_image_colour()).is_equal_to(VideoImage.BLUE)

        # destroy browser page without allowing shutdown hooks to run, then create new page
        await bob.recreate(unload_hooks=False)

        # happens after we reload the page so this won't go to the old stream

        await bob.set_video_image(VideoImage.GREEN)

        await bob.create_or_join(room_name)

        await bob.lobby_join()

        # Allow bob to start streaming as far as alice is concerned.
        await asyncio.sleep(3)

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        # ensure we don't have duplicate calls hanging around; and the video stream has been updated

        assert_that(alice_data.video_tiles).is_length(2)
        assert_that(bob_data.video_tiles).is_length(2)

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert_that(bob_tile.video_image_colour()).is_equal_to(VideoImage.GREEN)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert_that(alice_tile.video_image_colour()).is_equal_to(VideoImage.BLUE)
