import asyncio

from nio import AsyncClient

from trafficlight.client_types import ElementWeb, HydrogenWeb
from trafficlight.homerunner import HomeServer
from trafficlight.internals.client import MatrixClient
from trafficlight.internals.test import Test
from trafficlight.server_types import Synapse


class InviteUserDecryptPrejoinMessagesMoreUsersTest(Test):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementWeb()], "alice")
        self._client_under_test([ElementWeb()], "bob")

        self._client_under_test([HydrogenWeb()], "olivia")
        self._client_under_test([HydrogenWeb()], "liam")
        self._client_under_test([HydrogenWeb()], "charlotte")
        self._client_under_test([HydrogenWeb()], "james")
        self._client_under_test([HydrogenWeb()], "ava")
        self._client_under_test([HydrogenWeb()], "lucas")
        self._client_under_test([HydrogenWeb()], "isabella")
        self._client_under_test([HydrogenWeb()], "william")
        self._server_under_test(Synapse(), ["server"])

    async def run(
        self,
        alice: MatrixClient,
        bob: MatrixClient,
        olivia: MatrixClient,
        liam: MatrixClient,
        charlotte: MatrixClient,
        james: MatrixClient,
        ava: MatrixClient,
        lucas: MatrixClient,
        isabella: MatrixClient,
        william: MatrixClient,
        server: HomeServer,
    ) -> None:
        hydrogen_adapters = [
            olivia,
            liam,
            charlotte,
            james,
            ava,
            lucas,
            isabella,
            william,
        ]

        async def register(h: MatrixClient) -> None:
            await nio_client.register(h.localpart, h.password)

        async def login(h: MatrixClient) -> None:
            await h.login(server)

        nio_client = AsyncClient(server.cs_api)
        try:
            await asyncio.gather(*map(register, hydrogen_adapters))
            await asyncio.gather(*map(login, hydrogen_adapters))
            await asyncio.gather(alice.register(server), bob.register(server))

            await alice.create_room("little test room")
            await alice.change_room_history_visibility("invited")
            await alice.send_message(
                "Bob should not be able to read this, as he isn't invited yet"
            )
            await alice.invite_user(bob.localpart + ":" + server.server_name)
            for adapter in hydrogen_adapters:
                await alice.invite_user(adapter.localpart + ":" + server.server_name)
            await bob.accept_invite()
            message = "Everybody should be able to read this message!"
            await bob.send_message(message)
            await asyncio.gather(*map(lambda h: h.accept_invite(), hydrogen_adapters))
            await asyncio.gather(
                *map(lambda h: h.verify_message_in_timeline(message), hydrogen_adapters)
            )
        finally:
            await nio_client.close()
