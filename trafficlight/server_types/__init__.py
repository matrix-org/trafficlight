from typing import List

from trafficlight.homerunner import HomerunnerClient, HomeserverConfig


class ServerType(object):

    def name(self) -> str:
        return type(self).__name__

    def create(self, model_id: str, homerunner: HomerunnerClient) -> List[HomeserverConfig]:
        pass


class Synapse(ServerType):
    def create(self, model_id: str, homerunner: HomerunnerClient) ->  List[HomeserverConfig]:
        return homerunner.create(model_id, ["complement-synapse"])


class Dendrite(ServerType):
    def create(self, model_id: str, homerunner: HomerunnerClient) ->  List[HomeserverConfig]:
        return homerunner.create(model_id, ["complement-dendrite"])


class MixedFederation(ServerType):
    def create(self, model_id: str, homerunner: HomerunnerClient) ->  List[HomeserverConfig]:
        return homerunner.create(model_id, ["complement-dendrite", "complement-synapse"])
