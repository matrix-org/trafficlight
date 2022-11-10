from typing import List

from trafficlight.homerunner import HomerunnerClient, HomeServer


class ServerType(object):
    def name(self) -> str:
        return type(self).__name__

    def __repr__(self):
        return self.name()

    async def create(
        self, test_case_id: str, homerunner: HomerunnerClient
    ) -> List[HomeServer]:
        pass


class Synapse(ServerType):
    async def create(
        self, test_case_id: str, homerunner: HomerunnerClient
    ) -> List[HomeServer]:
        return await homerunner.create(test_case_id, ["complement-synapse"])


class Dendrite(ServerType):
    async def create(
        self, test_case_id: str, homerunner: HomerunnerClient
    ) -> List[HomeServer]:
        return await homerunner.create(test_case_id, ["complement-dendrite"])


class MixedFederation(ServerType):
    async def create(
        self, test_case_id: str, homerunner: HomerunnerClient
    ) -> List[HomeServer]:
        return await homerunner.create(
            test_case_id, ["complement-dendrite", "complement-synapse"]
        )
