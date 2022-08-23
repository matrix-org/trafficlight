from typing import List

from trafficlight.homerunner import HomeserverConfig
from trafficlight.store import Model, ModelState, Client
from trafficlight.tests._base import TestSuite


class SendMessagesTestSuite(TestSuite):

    def __init__(self):
        super(SendMessagesTestSuite, self).__init__(2, 1)

    def validate_model(self, model: Model):
        self.assertEqual(model.state, "completed")

        # TODO verify the model after completion, eg:
        #        self.assertEqual(model.data["alice_verified_crosssign"]['emoji'],
        #                        model.data["bob_verified_crosssign"]["emoji"],
        #                        "Emoji were not matching")

    def generate_model(self, clients: List[Client], servers: List[HomeserverConfig]) -> Model:
        alice = "alice"
        bob = "bob"

        clients[0].set_colour(alice)
        clients[0].set_model(model)
        clients[1].set_colour(bob)
        clients[1].set_model(model)


        import uuid as guid

        model_id = str(guid.uuid4())
        # Generating server
        random_user = "user_" + str(guid.uuid4())
        docker_api = servers[0].cs_api.replace("localhost", "10.0.2.2")

        login_data = {
            "username": random_user,
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": servers[0].cs_api,
            },
        }

        # maybe factor out the above, maybe not...
        model = Model(
            self.test_id,
            [
                ModelState(
                    "init_r",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data,
                            "responses": {"registered": "init_g"},
                        },
                    },
                ),
                ModelState(
                    "init_g",
                    {
                        bob: {
                            "action": "login",
                            "data": login_data,
                            "responses": {"loggedin": "start_crosssign"},
                        }
                    },
                ),
                ModelState(
                    "start_crosssign",
                    {
                        bob: {
                            "action": "start_crosssign",
                            "responses": {"started_crosssign": "accept_crosssign"},
                        }
                    },
                ),
                ModelState(
                    "accept_crosssign",
                    {
                        alice: {
                            "action": "accept_crosssign",
                            "responses": {"accepted_crosssign": "verify_crosssign_rg"},
                        }
                    },
                ),
                ModelState(
                    "verify_crosssign_rg",
                    {
                        alice: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "verify_crosssign_g"},
                        },
                        bob: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "verify_crosssign_r"},
                        },
                    },
                ),
                ModelState(
                    "verify_crosssign_r",
                    {
                        alice: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "complete"},
                        }
                    },
                ),
                ModelState(
                    "verify_crosssign_g",
                    {
                        bob: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "complete"},
                        }
                    },
                ),
                ModelState(
                    "complete",
                    {
                        alice: {"action": "exit", "responses": {}},
                        bob: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "init_r",
        )
        model.on_enter_completed =

        model.calculate_transitions()


        return model
