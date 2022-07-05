# vim: expandtab ts=4:
import functools
import logging
logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted
logging.getLogger('transitions').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from transitions import Machine, State

bp = Blueprint("client", __name__, url_prefix="/client")

class ColouringState(object):
    def __init__(self, name, action_map):
       self.name = name
       self.action_map = action_map
 
class ColouringTestCase(object):
    def __init__(self, clients, state_list,  initial_state):
        self.clients = {}
        for client in clients:
            print (client)
            self.clients.update({client: None})

        states = []
        state_map = {}
        for state in state_list:
            states.append(state.name)
            state_map[state.name] = state

        self.machine = Machine(
            model=self, states=states, initial = initial_state
        )
        
        self.state_map = state_map
        self.generic_action = {"action": "idle", "responses": []}

    def action_for(self, uuid):
        colour = self.lookup(uuid)
        action_map = self.state_map.get(self.state).action_map
        specific_action = action_map.get(colour)
        if specific_action is None:
            return self.generic_action
        return specific_action

    def add_transition(self, trigger, source, destination):
        self.machine.add_transition(trigger, source, destination)

    def lookup(self, uuid):
        # Does python have a two way map ? TODO
        for client in self.clients:
            if self.clients.get(client) == uuid:
                return client

        # Didn't find it, allocate one
        for client in self.clients.keys():
            if self.clients.get(client) is None:
                self.clients[client] = uuid
                return client

        # Didn't find it and there's no more spots, return None
        return None

    def transition(self, uuid, update):

        colour = self.lookup(uuid)
        transition = colour + "_" + update['response']
        self.trigger(transition)


@bp.route("/<string:uuid>/poll", methods=["GET"])
def poll(uuid):
    action = model.action_for(uuid)
    # action is some json
    if action is None:
        action = {"action": "unexpected", "responses": []}
    colour = model.lookup(uuid)
    logger.info("%s (%s) polled: %s", uuid, colour, action)

    return action


@bp.route("/<string:uuid>/respond", methods=["POST"])
def respond(uuid):
    update = request.json
    colour = model.lookup(uuid)
    logger.info("%s (%s) responded: %s", uuid, colour, update)
    model.transition(uuid, update)

    return {}

# TODO this should be some sort of externally provided test case, but for now:


## I think, actually, that we can just import from json all the below as little test cases.
## But for now: this.

model = ColouringTestCase(
    ["red", "green"],  # clients
    [
        ColouringState("init_rg", {"red": {"action": "ready"}, "green": {"action": "ready"}}),
        ColouringState("init_r", {"red": {"action": "ready"}}),
        ColouringState("init_g", {"green": {"action": "ready"}}),
        ColouringState(
            "start_crosssign",
            {"red": {"action": "start_crosssign", "responses": ["started_crosssign"]}},
        ),
        ColouringState("accept_crosssign", {"green": {"action": "accept_crosssign", "responses": ["accepted_crosssign"]}}),
        ColouringState(
            "verify_crosssign_rg",
            {
                "red": {"action": "verify_crosssign"},
                "green": {"action": "verify_crosssign"},
            },
        ),
        ColouringState("verify_crosssign_r", {"red": {"action": "verify_crosssign"}}),
        ColouringState("verify_crosssign_g", {"green": {"action": "verify_crosssign"}}),
        ColouringState(
            "complete", {"red": {"action": "exit"}, "green": {"action": "exit"}}
        )
    ],
    "init_rg"
)

model.add_transition("red_ready", "init_rg", "init_g")
model.add_transition("red_ready", "init_r", "start_crosssign")
model.add_transition("green_ready", "init_rg", "init_r")
model.add_transition("green_ready", "init_g", "start_crosssign")

model.add_transition("red_started_crosssign", "start_crosssign", "accept_crosssign")
model.add_transition(
    "green_accepted_crosssign", "accept_crosssign", "verify_crosssign_rg"
)
model.add_transition(
    "green_verified_crosssign", "verify_crosssign_rg", "verify_crosssign_r"
)
model.add_transition("green_verified_crosssign", "verify_crosssign_g", "complete")
model.add_transition(
    "red_verified_crosssign", "verify_crosssign_rg", "verify_crosssign_g"
)
model.add_transition("red_verified_crosssign", "verify_crosssign_r", "complete")
