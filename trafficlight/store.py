# vim: expandtab ts=4:
# Copyright 2022 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools
import logging
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

from transitions import Machine, State

from transitions.extensions import GraphMachine
from transitions.extensions.states import add_state_features, Tags, Timeout

class Client(object):
    def __init__(self, uuid, registration):
       self.uuid = uuid
       self.registration = registration
       self.model = None
       self.last_polled = None
       self.last_responded = None
       self.registered = datetime.now()
       self.completed = False
 
    def __str__(self):
       return f"Client {self.uuid} Model {self.model} Registration {self.registration}"

    def poll(self, update_last_polled=True):
       if self.model is None:
           # No model has been allocated yet; idle.
           return {"action": "idle", "responses": []}
       
       if self.completed:
           # Client has finished work, exit
           return {"action": "exit", "responses": []}
      
       action = self.model.action_for(self.uuid)
       # action is some json
       if action is None:
           action = {"action": "unexpected", "responses": []}
       colour = self.model.lookup(self.uuid)
       logger.info("%s (%s) polled: %s", self.uuid, colour, action)
       if (update_last_polled):
           self.last_polled = datetime.now()
       return action

    def respond(self, update, update_last_responded=True):
       if self.model is None:
           raise Error("Client %s has not been assigned a model yet", self.uuid)
       
       colour = self.model.lookup(self.uuid)
       logger.info("%s (%s) responded: %s", self.uuid, colour, update)
       self.model.transition(self.uuid, update)
       if (update_last_responded):
           self.last_responded = datetime.now()

    def set_model(self, model):
       logger.info("Set model %s on %s", model.uuid, self.uuid)
       self.model = model

    def set_colour(self, colour):
       logger.info("Set colour %s on %s", colour, self.uuid)
       self.colour = colour

    def completed(self):
       self.completed = True

class ColouringState(object):
    def __init__(self, name, action_map):
       self.name = name
       self.action_map = action_map

@add_state_features(Timeout)
class TimeoutGraphMachine(GraphMachine):
    pass

class Model(object):
    def __init__(self, uuid, state_list,  initial_state):
        self.uuid = uuid
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
        self.completed = False

    def __str__(self):
       return f"Model {self.uuid} Clients {self.clients}"

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

    def render_whole_graph(self, bytesio):
        self.get_graph().draw(bytesio, format="png", prog='dot')

    def render_local_region(self, bytesio):
        self.get_graph(show_roi=True).draw(bytesio, format="png", prog='dot')

    def add_client(self, colour, client):
        client.set_model(self)
        client.set_colour(colour)
        self.clients.append(client)

    def on_enter_completed(self):
        for client in self.clients:
            client.completed()
        self.completed = True

clients = []
tests = []

def get_tests():
   return tests

def get_test(uuid):
   for test in tests:
      if str(test.uuid) == str(uuid):
         return test
      else: 
         logger.info("%s did not match %s", test.uuid, uuid)
   return None

def get_clients():
   return clients

def add_client(client):
   clients.append(client)

def add_test(test):
   tests.append(test)

# Probably move me elsewhere soon...

## I think, actually, that we can just import from json all the below as little test cases.
## But for now: this.

def generate_model(clients):
    red_client = clients[0]
    green_client = clients[1]
    import uuid as guid
    random_user = "user_"+str(guid.uuid4())
    logging.info("User for test "+random_user)
    RED = "red"
    GREEN = "green" 
    login_data = { "username": random_user, "password": "bubblebobblebabble", "homeserver_url": { "local_docker": "http://10.0.2.2:8080/", "local": "http://localhost:8080/"} }
    model_uuid = "model_"+str(guid.uuid4())
    model = Model(
        model_uuid,
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

    model.add_client(RED, red_client)
    model.add_client(GREEN, green_client)
    return model
