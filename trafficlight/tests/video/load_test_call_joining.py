from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage, VideoTile
from trafficlight.internals.test import Test

import asyncio
from datetime import datetime
from assertpy import assert_that, soft_assertions


# Tests

class JoinCallReceiveVideoTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(
            self, alice: ElementCallClient, bob: ElementCallClient
    ) -> None:
        await alice.register()

        await bob.guest_user();

        await asyncio.gather(alice.set_display_name(), bob.set_display_name())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        # Create room
        await alice.create_or_join(room_name)

        lobby_data = await alice.get_lobby_data()

        for i in range(1, 100):
            if i % 3 == 0:
                await alice.set_video_image(VideoImage.RED)
                await bob.set_video_image(VideoImage.GREEN)
            else:
                await alice.set_video_image(VideoImage.GREEN)
                await bob.set_video_image(VideoImage.BLUE)

            await bob.join_by_url(lobby_data.invite_url)

            await bob.lobby_join()
            await bob.set_display_name(f"bob{i}")

            alice_data = await alice.get_call_data()
            bob_data = await bob.get_call_data()

            with soft_assertions():

                # Ensure we don't gain or lose members doing this.
                assert_that(alice_data.video_tiles).is_length(2)
                assert_that(bob_data.video_tiles).is_length(2)

                assert_that(alice_data.get_video_tile_by_caption(f"bob{i}")).is_true()

            # Ensure we don't lose display names doing this.

        await asyncio.gather(alice.create_or_join(room_name), bob.create_or_join(room_name))
        # lobby screen
        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        await asyncio.gather(alice.set_video_image(VideoImage.BLUE), bob.set_video_image(VideoImage.RED))

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        assert len(alice_data.video_tiles) == 2
        assert len(bob_data.video_tiles) == 2

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert bob_tile.video_image_is(VideoImage.RED)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert alice_tile.video_image_is(VideoImage.BLUE)

        await alice.set_video_image(VideoImage.GREEN)
        bob_data = await bob.get_call_data()

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert alice_tile.video_image_is(VideoImage.GREEN)
