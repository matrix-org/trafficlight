# vim: expandtab ts=4:
import functools
import logging
import uuid
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# Urgh, refactor so there's a list of client matches, and the model_generator takes a list of clients in the same order.
# Additionally, refactor so matchers are more descriptive and can explain why the test isn't running
# Maybe a hamcrest/matcher but for python type thing would do well here

class TestCase(object):
    def __init__(self, description, client_matchers, model_generator):
       self.uuid = uuid.uuid4()
       self.description = description
       self.client_matchers = client_matchers
       self.model_generator = model_generator
       self.registered = datetime.now()
       self.running = False
       self.model = None

    def __str__(self):
       return f"TestCase {self.description} {self.uuid} Model {self.model} Running {self.running}"

    # takes a client list and returns clients required to run the test
    def runnable(self, client_list):
       if len(self.client_matchers) == 2:
          # there's a better way to do this for N clients.
          red_clients = list(filter(self.client_matchers[0], client_list))
          green_clients = list(filter(self.client_matchers[1], client_list))
   
          if len(red_clients) > 0:
             for red_client in red_clients:
                for green_client in green_clients:
                   if red_client != green_client:
                        return [red_client, green_client]

       return None

    def run(self, client_list):
       if self.running:
          raise Error("Logic error: already running this test")
       else:
          self.running = True
       # tidy this up somewhat
       self.model = self.model_generator(client_list)
