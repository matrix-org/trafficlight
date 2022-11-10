import logging
from typing import List

from trafficlight.client_types import ElementAndroid, ElementWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import Client
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class Room:
    def __init__(self, name: str):
        self.name = name
        self.id = None


class Poll:
    def __init__(self, room: Room, question: str, options: List[str]):
        self.room = room
        self.question = question
        self.options = options


logger = logging.getLogger(__name__)


class AlternativeTestExample(Test):
    async def mass_join_action(self, room: Room, users: int):
        pass
        # todo using asyncio and matrix client create 1000 random users in python
        # and make them all join a room

    def __init__(self):
        super().__init__()
        self._client_under_test([ElementWeb(), ElementAndroid()], "alice")
        self._client_under_test([ElementWeb(), ElementAndroid()], "bob")
        # Nearly there ..
        self._server_under_test(Synapse(), ["server"])

    async def run(self, alice: Client, bob: Client, server: HomeServer) -> None:
        """
        Run: called after an adapter is found for each client and a homeserver instance has been created.
        @return:
        """
        logger.info(f"{alice} {bob}, {server}")
        print("whoo")
        await alice.register(server)
        await bob.register(server)

        room: Room = await alice.create_room("Poll Test Room")

        await bob.join(room)

        await self.mass_join_action(room, 1000)

        poll: Poll = await alice.create_poll(
            room, "What is the price of things", ["one", "two", "three", "four"]
        )

        print(poll.id)
