class RemoteException(Exception):
    def __init__(self, details: str, path: str):
        self.formatted_message = (
            f"{self.__class__.__name__} from adapter\n{details}\nIn file {path}\n"
        )


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


class PollTimeoutException(Exception):
    """
    Raised when the adapter hasn't contacted the server recently.

    Generated internally if no response is done fast enough.
    """

    pass


class ShutdownException(Exception):
    """
    Raised when the server is shutdown.

    Generated only on server shutdown.
    """

    pass
