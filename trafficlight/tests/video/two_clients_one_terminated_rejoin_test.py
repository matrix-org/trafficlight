from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient, VideoImage, VideoTile
from trafficlight.internals.test import Test

import asyncio
from datetime import datetime


# Does not match any item in the spreadsheet

class TwoClientsOneTerminatedAndRejoin(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(
            self, alice: ElementCallClient, bob: ElementCallClient
    ) -> None:

        await asyncio.gather(alice.register(), bob.register())

        await asyncio.gather(alice.set_display_name(), bob.set_display_name())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        await asyncio.gather(alice.create_or_join(room_name), bob.create_or_join(room_name))

        # lobby screen
        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        await alice.set_video_image(VideoImage.BLUE)
        await bob.set_video_image(VideoImage.RED)


        alice_data = await alice.get_call_data()
        assert len(alice_data.video_tiles) == 2

        bob_data = await alice.get_call_data()
        assert len(bob_data.video_tiles) == 2

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert bob_tile.video_image_is(VideoImage.RED)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert alice_tile.video_image_is(VideoImage.BLUE)

        # destroy browser page without allowing shutdown hooks to run, then create new page
        await bob.recreate(unload_hooks=False)

        # happens after we reload the page so this won't go to the old stream

        await bob.set_video_image(VideoImage.GREEN)

        await bob.create_or_join(room_name)

        await bob.lobby_join();

        alice_data = await alice.get_call_data()
        bob_data = await bob.get_call_data()

        # ensure we don't have duplicate calls hanging around; and the video stream has been updated

        assert len(alice_data.video_tiles) == 2
        assert len(bob_data.video_tiles) == 2

        bob_tile = alice_data.get_video_tile_by_caption(bob.display_name)
        assert bob_tile.video_image_is(VideoImage.GREEN)

        alice_tile = bob_data.get_video_tile_by_caption(alice.display_name)
        assert alice_tile.video_image_is(VideoImage.BLUE)

        
