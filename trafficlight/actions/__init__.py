from typing import Dict

from . import Action


class Action:
    def __init__(self, name: str, data: Dict[str, Any]) -> None:
        self.name = name
        self.data = data


class Response:
    def __init__(self, name: str) -> None:
        self.name = name


REGISTERED = Response("registered")


def register(username: str, password: str, homeserver_urls: Dict[str, str], responses: Dict[Response, str]) -> Action:
    """
    Registration requires clients not to be logged in.
    Registration should create an account and move forward through all options (eg analytics optins, client naming,
    until the client has got to the base screen of the client.
    """

    return Action(
        "register",
        {
            "user": username,
            "pass": password,
            "homeserver_urls": homeserver_urls
        },
        responses
    )


LOGGEDIN = Response("loggedin")


def login(username: str, password: str, homeserver_urls: Dict[str, str], responses: Dict[Response, str]) -> Action:
    """
    Login requires clients not to be logged in.
    Login should move forward through all options (eg analytics optins, client naming,
    until the client has got to the base screen of the client.
    Login should not perform any client verification or restoration of encryption keys.
    """

    return Action(
        "login",
        {
            "user": username,
            "pass": password,
            "homeserver_urls": homeserver_urls
        },
        responses
    )


def idle(delay: int = 5000) -> Action:
    """
    Idle can be used in any situation
    Clients should wait for the given delay and poll again without taking any further action
    """
    return Action(
        "idle",
        {
            "delay": delay
        }
    )


STARTED_CROSSSIGN = Response("started_crosssign")


def start_crosssign(responses: Dict[Response, str]) -> Action:
    """
    Should be used when in the rest state after login or registration
    Should start verification
    Should stop once request to other device has been made.
    """
    return Action(
        "start_crosssign",
        {},
        responses
    )


ACCEPTED_CROSSSIGN = Response("accepted_crosssign")


def accept_crosssign(responses: Dict[Response, str]) -> Action:
    """
    Should be used in the rest state after login or registration.
    Should wait for a verification request to come from another device
    Should accept the verification request (but not perform the verification emoji match etc)
    """
    return Action(
        "accept_crosssign",
        {},
        responses
    )


VERIFIED_CROSSSIGN = Response("verified_crosssign")


def verify_crosssign_emoji(responses: Dict[Response, str]) -> Action:
    """
    Should be performed by a client either after starting (and having the verification accepted) OR just after accepting.
    Should verify the crosssign (and return the emoji in the response for confirmation)
    Should stop once verification has been accepted and client is back to the rest state.
    """
    return Action(
        "verify_crosssign_emoji",
        {},
        responses
    )


def client_exit() -> Action:
    """
    Can be used at any time
    Client should terminate the test run, clear data and (optionally) reset for the next run or exit.
    Client should take no further actions and not poll again.
    """
    return Action(
        "exit",
        {},
        {}
    )


## Not really used but here as a template.
def sample(responses: Dict[Response, str]) -> Action:
    """
    Sample can be used when?
    Sample should take which action?
    Sample should stop when?
    """
    return Action(
        "",
        {},
        responses
    )
