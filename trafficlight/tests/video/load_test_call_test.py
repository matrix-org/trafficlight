import asyncio
from datetime import datetime

from assertpy import assert_that, soft_assertions  # type: ignore

from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage
from trafficlight.internals.test import Test

# Tests


class LoadTestCallTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        await asyncio.gather(alice.register(), bob.register())

        await asyncio.gather(alice.set_display_name(), bob.set_display_name())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        # Create room
        await alice.create_or_join(room_name)

        lobby_data = await alice.get_lobby_data()

        await alice.lobby_join()

        for i in range(1, 10):
            if i % 2 == 0:
                alice_colour = VideoImage.RED
                bob_colour = VideoImage.GREEN
            else:
                alice_colour = VideoImage.GREEN
                bob_colour = VideoImage.BLUE

            await asyncio.gather(
                alice.set_video_image(alice_colour), bob.set_video_image(bob_colour)
            )

            await bob.join_by_url(lobby_data.invite_url)
            await bob.lobby_join()
            # Let's keep cycling bob's display name
            await bob.set_display_name(f"bob{i}")

            (alice_data, bob_data) = await asyncio.gather(
                alice.get_call_data(), bob.get_call_data()
            )

            with soft_assertions():

                # Ensure we don't gain or lose members doing this.
                assert_that(alice_data.video_tiles).is_length(2)
                assert_that(bob_data.video_tiles).is_length(2)
                assert_that(
                    alice_data.get_video_tile_by_caption(f"bob{i}")
                ).is_not_none()
                assert_that(
                    alice_data.get_video_tile_by_caption(f"bob{i}").video_image_colour()
                ).is_equal_to(bob_colour)
                assert_that(
                    bob_data.get_video_tile_by_caption("alice").video_image_colour()
                ).is_equal_to(alice_colour)

                # assert that alice colour == alice_colour and bob colour = bob_colour...

            await bob.leave_call()
            # Ensure we don't lose display names doing this.
