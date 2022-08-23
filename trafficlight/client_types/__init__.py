from trafficlight import Client


class ClientType(object):
    def match(self, x: Client) -> bool:
        pass


class ElementWeb(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-web"


class ElementAndroid(ClientType):
    def match(self, x: Client) -> bool:
        return str(x.registration["type"]) == "element-android"
