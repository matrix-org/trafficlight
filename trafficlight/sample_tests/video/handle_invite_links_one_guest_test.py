from trafficlight.client_types import ElementCall
from trafficlight.internals.client import ElementCallClient
from trafficlight.internals.test import Test
from trafficlight.sample_tests.video.handle_invite_base import InviteLinksMixin


class OneRegisteredInviteLinksTest(Test, InviteLinksMixin):
    def __init__(self) -> None:
        super().__init__()
        self._client_under_test([ElementCall()], "alice")
        self._client_under_test([ElementCall()], "bob")

    async def run(self, alice: ElementCallClient, bob: ElementCallClient) -> None:
        await alice.register()
        await bob.guest_user()
        await alice.set_display_name()
        await self._run_test(alice, bob)
