from trafficlight.internals.adapter import Adapter


class ClientType(object):
    def name(self) -> str:
        return type(self).__name__

    def match(self, x: Adapter) -> bool:
        pass

    def __repr__(self) -> str:
        return self.name()


class ElementWeb(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-web"


class ElementAndroid(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-android"


class ElementIos(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "element-ios"


class NetworkProxy(ClientType):
    def match(self, x: Adapter) -> bool:
        return str(x.registration["type"]) == "network-proxy"
