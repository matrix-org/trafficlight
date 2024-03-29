import asyncio
from datetime import datetime

from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient
from trafficlight.internals.test import Test

# Known-broken at the moment.


class SpotlightTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        await asyncio.gather(alice.register(), bob.register())

        room_name = "tl_chat_" + str(datetime.now().timestamp())

        await alice.create(room_name)
        alice_lobby = await alice.get_lobby_data()

        await bob.join_by_url(alice_lobby.invite_url)

        # lobby screen
        await asyncio.gather(alice.lobby_join(), bob.lobby_join())
        await asyncio.sleep(5)

        # Soundcard use is not available yet.

        #
        # await alice.start_sine_wave()

        #
        # bob_data = await bob.get_call_data()

        # alice_tile = cast(VideoTile, bob_data.video_tiles.getByCaption("alice"))
        #
        # assert alice_tile.speaking_indicator [green bit on the side]
        # assert not bob_tile.speaking_indicator
        #
        # alice_tile = cast(VideoTile, alice_data.video_tiles.getByCaption("bob"))
        # assert rgb(0, 255, 0) == get_predomininant_colour(alice_tile.snapshot_file)
        #
        #
        # await alice.set_video_image(VideoImage.GREEN)
        # bob_data = await bob.get_call_data()
        # assert rgb(0,0,255) == get_predomininant_colour(bob_tile.snapshot_file)
