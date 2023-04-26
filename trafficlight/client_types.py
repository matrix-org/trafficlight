from trafficlight.internals.adapter import Adapter


class ClientType(object):
    def name(self) -> str:
        return type(self).__name__

    def match(self, x: Adapter) -> bool:
        pass

    def __repr__(self) -> str:
        return self.name()


class ElementWebStable(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-web"


class ElementWebDevelop(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-web"


class HydrogenWeb(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "hydrogen-web"


class ElementAndroid(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-android"


class ElementIos(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-ios"


class ElementCall(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-call"


class NetworkProxy(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "network-proxy"
