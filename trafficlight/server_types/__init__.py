from trafficlight.homerunner import HomerunnerClient


class ServerType(object):
    def create(self, model_id, homerunner: HomerunnerClient) -> bool:
        pass


class Synapse(ServerType):
    def create(self, model_id, homerunner: HomerunnerClient) -> bool:
        return homerunner.create(model_id, ["complement-synapse"])


class Dendrite(ServerType):
    def create(self, model_id, homerunner: HomerunnerClient) -> bool:
        return homerunner.create(model_id, ["complement-dendrite"])


class MixedFederation(ServerType):
    def create(self, model_id, homerunner: HomerunnerClient) -> bool:
        return homerunner.create(model_id, ["complement-dendrite", "complement-synapse"])
