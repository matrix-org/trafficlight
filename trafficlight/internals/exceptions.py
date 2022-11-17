class RemoteException(Exception):
    def __init__(self, details: str, path: str):
        self.formatted_message = f"{self.__class__.__name__} from adapter\n{details}\nIn file {path}\n"

class ActionException(RemoteException):
    """
    Raised when an action on an adapter fails
    Generated when "type": "action"
    """
    pass


class AdapterException(RemoteException):
    """
    Raised when the adapter itself fails.

    Generated when "type": is not "action".
    """
    pass
