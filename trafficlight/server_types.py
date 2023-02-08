from typing import List


class ServerType(object):
    def name(self) -> str:
        return type(self).__name__

    def complement_types(self) -> List[str]:
        pass

    def __repr__(self) -> str:
        return self.name()


class SynapseStable(ServerType):
    def complement_types(self) -> List[str]:
        return ["ghcr.io/matrix-org/synapse/complement-synapse:master"]


class SynapseDevelop(ServerType):
    def complement_types(self) -> List[str]:
        return ["ghcr.io/matrix-org/synapse/complement-synapse:develop"]


class Dendrite(ServerType):
    def complement_types(self) -> List[str]:
        return ["complement-dendrite"]


class TwoSynapseFederation(ServerType):
    def complement_types(self) -> List[str]:
        return [
            "ghcr.io/matrix-org/synapse/complement-synapse:develop",
            "ghcr.io/matrix-org/synapse/complement-synapse:develop",
        ]
