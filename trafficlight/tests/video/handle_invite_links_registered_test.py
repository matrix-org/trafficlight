from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient
from trafficlight.tests.video.handle_invite_base import InviteLinksMixin
from trafficlight.internals.test import Test


class TwoRegisteredInviteLinksTest(Test, InviteLinksMixin):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(
            self, alice: ElementCallClient, bob: ElementCallClient
    ) -> None:
        await alice.register()
        await bob.register()
        await alice.set_display_name()
        await bob.set_display_name()
        await self._run_test(alice, bob)


