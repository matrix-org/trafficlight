# vim: expandtab ts=4:
import functools
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

from transitions import Machine, State

from transitions.extensions import GraphMachine

class Client(object):
    def __init__(self, uuid, registration):
       self.uuid = uuid
       self.registration = registration
       self.model = None

    def poll(self):
       if self.model is None:
           # No model has been allocated yet; idle.
           return {"action": "idle", "responses": []}
      
       action = self.model.action_for(self.uuid)
       # action is some json
       if action is None:
           action = {"action": "unexpected", "responses": []}
       colour = self.model.lookup(self.uuid)
       logger.info("%s (%s) polled: %s", self.uuid, colour, action)
    
       return action

    def respond(self, update):
       if self.model is None:
           raise Error("Client has not been assigned a model yet")
       
       colour = self.model.lookup(self.uuid)
       logger.info("%s (%s) responded: %s", self.uuid, colour, update)
       self.model.transition(self.uuid, update)

    def set_model(self, model):
       self.model = model

    def set_colour(self, colour):
       self.colour = colour

class ColouringState(object):
    def __init__(self, name, action_map):
       self.name = name
       self.action_map = action_map
 
class ColouringTestCase(object):
    def __init__(self, state_list,  initial_state):
        states = []
        state_map = {}
        for state in state_list:
            states.append(state.name)
            state_map[state.name] = state

        self.machine = GraphMachine(
            model=self, states=states, initial = initial_state
        )
        
        self.state_map = state_map
        self.generic_action = {"action": "idle", "responses": []}
        # list of clients
        self.clients = []

    def action_for(self, uuid):
        client = self.lookup(uuid)
        state_obj = self.state_map.get(self.state)
        action_map = state_obj.action_map
        specific_action = action_map.get(client.colour)
        if specific_action is None:
            return self.generic_action
        return specific_action

    def calculate_transitions(self):
        for name, state in self.state_map.items():
           for colour, action in state.action_map.items():
              for action, destination in action['responses'].items():
                 logger.info("Adding %s - %s_%s -> %s", name, colour, action, destination)
                 self.add_transition(colour+"_"+action, name, destination)

    def add_transition(self, trigger, source, destination):
        self.machine.add_transition(trigger, source, destination)

    def lookup(self, uuid):
        for client in self.clients:
            if client.uuid == uuid:
               return client
        return None

    def transition(self, uuid, update):

        client = self.lookup(uuid)
        transition = client.colour + "_" + update['response']
        old_state = self.state
        self.trigger(transition)
        new_state = self.state
        logger.info("State transition %s to %s ( via %s )", old_state, new_state, transition )

    def render_whole_graph(self, output_file):
        self.get_graph().draw(output_file, prog='dot')

    def render_local_region(self, output_file):
        self.get_graph(show_roi=True).draw(output_file, prog='dot')

    def add_client(self, colour, client):
        client.set_model(self)
        client.set_colour(colour)
        self.clients.append(client)






# TODO this should be some sort of externally provided test case, but for now:


## I think, actually, that we can just import from json all the below as little test cases.
## But for now: this.

def generate_model(red, green):
    import uuid as guid
    random_user = "user_"+str(guid.uuid4())
    logging.info("User for test "+random_user)
    RED = "red"
    GREEN = "green" 
    login_data = { "username": random_user, "password": "bubblebobblebabble", "homeserver_url": { "local_docker": "http://10.0.2.2:8080/", "local": "http://localhost:8080/"} }
    
    model = ColouringTestCase(
        [
            ColouringState("init_r", 
                {
                    RED: {"action": "register", "data": login_data, "responses": {"registered": "init_g"}},
                }
            ),
            ColouringState("init_g", 
                {
                    GREEN: {"action": "login", "data": login_data, "responses": {"loggedin": "start_crosssign"}}
                }
            ),
            ColouringState(
                "start_crosssign",
                {
                     GREEN: {"action": "start_crosssign", "responses": {"started_crosssign": "accept_crosssign"}}
                },
            ),
            ColouringState(
                "accept_crosssign",
                {
                    RED: {"action": "accept_crosssign", "responses": {"accepted_crosssign": "verify_crosssign_rg"}}
                }
            ),
            ColouringState(
                "verify_crosssign_rg",
                {
                    RED: {"action": "verify_crosssign_emoji", "responses": {"verified_crosssign": "verify_crosssign_g"}},
                    GREEN: {"action": "verify_crosssign_emoji", "responses": {"verified_crosssign": "verify_crosssign_r"}},
                },
            ),
            ColouringState(
                "verify_crosssign_r",
                {
                    RED: {"action": "verify_crosssign_emoji", "responses": {"verified_crosssign": "complete"}}
                }
            ),
            ColouringState(
                "verify_crosssign_g",
                {
                    GREEN: {"action": "verify_crosssign_emoji", "responses": {"verified_crosssign": "complete"}}
                }
            ),
            ColouringState(
                "complete", {RED: {"action": "exit", "responses":{}}, GREEN: {"action": "exit", "responses":{}}}
            )
        ],
        "init_r"
    )
    model.calculate_transitions()

    model.add_client(RED, red)
    model.add_client(GREEN, green)
    return model

#model.render_whole_graph('/tmp/model.png')
