from trafficlight.objects.client import Client


class ClientType(object):
    def name(self) -> str:
        return type(self).__name__

    def match(self, x: Client) -> bool:
        pass


class ElementWeb(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-web"


class HydrogenWeb(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "hydrogen-web"


class ElementAndroid(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-android"


class NetworkProxy(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "network-proxy"
