from typing import List

from trafficlight.homerunner import HomerunnerClient, HomeserverConfig


class ServerType(object):
    def name(self) -> str:
        return type(self).__name__

    async def create(
        self, model_id: str, homerunner: HomerunnerClient
    ) -> List[HomeserverConfig]:
        pass


class Synapse(ServerType):
    async def create(
        self, model_id: str, homerunner: HomerunnerClient
    ) -> List[HomeserverConfig]:
        return await homerunner.create(model_id, ["complement-synapse"])


class Dendrite(ServerType):
    async def create(
        self, model_id: str, homerunner: HomerunnerClient
    ) -> List[HomeserverConfig]:
        return await homerunner.create(model_id, ["complement-dendrite"])


class MixedFederation(ServerType):
    async def create(
        self, model_id: str, homerunner: HomerunnerClient
    ) -> List[HomeserverConfig]:
        return await homerunner.create(
            model_id, ["complement-dendrite", "complement-synapse"]
        )
