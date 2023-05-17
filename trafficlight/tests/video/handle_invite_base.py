import asyncio
from datetime import datetime

from assertpy import assert_that, soft_assertions  # type: ignore

from trafficlight.internals.client import ElementCallClient, VideoImage


class InviteLinksMixin:
    async def _run_test(
        self, creator: ElementCallClient, joiner: ElementCallClient
    ) -> None:
        room_name = "tl_chat_" + str(datetime.now().timestamp())

        await creator.set_video_image(VideoImage.RED)
        await joiner.set_video_image(VideoImage.BLUE)

        await creator.create_or_join(room_name)

        creator_lobby_data = await creator.get_lobby_data()
        assert_that(creator_lobby_data.call_name).is_equal_to(room_name)

        # Now join bob to the call before alice joins the call via page_url

        await joiner.join_by_url(creator_lobby_data.page_url)

        joiner_lobby_data = await joiner.get_lobby_data()

        with soft_assertions():
            # Check bob sees the same things as alice
            assert_that(joiner_lobby_data.call_name).is_equal_to(room_name)
            assert_that(joiner_lobby_data.page_url).is_equal_to(
                creator_lobby_data.page_url
            )
            assert_that(joiner_lobby_data.invite_url).is_equal_to(
                creator_lobby_data.invite_url
            )

        # Now join bob to the call before alice joins the call via invite_url

        await joiner.join_by_url(creator_lobby_data.invite_url)

        joiner_lobby_data = await joiner.get_lobby_data()

        with soft_assertions():
            # Check bob sees the same things as alice
            assert_that(joiner_lobby_data.call_name).is_equal_to(room_name)
            assert_that(joiner_lobby_data.page_url).is_equal_to(
                creator_lobby_data.page_url
            )
            assert_that(joiner_lobby_data.invite_url).is_equal_to(
                creator_lobby_data.invite_url
            )

        await creator.lobby_join()

        creator_call_data = await creator.get_call_data()

        with soft_assertions():
            # check that everything remains the same after joining the call
            assert_that(creator_call_data.page_url).is_equal_to(
                creator_lobby_data.page_url
            )
            assert_that(creator_call_data.invite_url).is_equal_to(
                creator_lobby_data.invite_url
            )
            assert_that(creator_call_data.call_name).is_equal_to(
                creator_lobby_data.call_name
            )

        # Now join bob to the call when the room has been created

        await joiner.join_by_url(creator_call_data.invite_url)

        joiner_lobby_data = await joiner.get_lobby_data()

        with soft_assertions():
            # Check bob sees the same things as alice
            assert_that(joiner_lobby_data.call_name).is_equal_to(room_name)
            assert_that(joiner_lobby_data.page_url).is_equal_to(
                creator_lobby_data.page_url
            )
            assert_that(joiner_lobby_data.invite_url).is_equal_to(
                creator_lobby_data.invite_url
            )

        await joiner.lobby_join()

        # allow call to settle.
        await asyncio.sleep(7)

        joiner_call_data = await joiner.get_call_data()
        creator_call_data = await creator.get_call_data()

        assert joiner_call_data.call_name == room_name
        assert joiner_call_data.invite_url == creator_call_data.invite_url
        assert joiner_call_data.page_url == creator_call_data.page_url

        # Check video feeds are still working after all this confusion.
        assert_that(
            joiner_call_data.get_video_tile_by_caption(
                creator.display_name
            ).video_image_colour()
        ).is_equal_to(VideoImage.RED)
        assert_that(
            creator_call_data.get_video_tile_by_caption(
                joiner.display_name
            ).video_image_colour()
        ).is_equal_to(VideoImage.BLUE)
