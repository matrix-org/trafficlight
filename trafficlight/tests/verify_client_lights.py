from _base import TwoClientsOneServerTestCase
from trafficlight.store import Model, ModelState


class VerifyClientLights(TwoClientsOneServerTestCase):

    def validate_results(self, model):
        self.assertEqual(model.state, "completed")

        # TODO verify the model after completion, eg:
        #        self.assertEqual(model.data["alice_verified_crosssign"]['emoji'],
        #                        model.data["bob_verified_crosssign"]["emoji"],
        #                        "Emoji were not matching")

    def generate_model(self, homeserver, client_one, client_two) -> Model:
        alice = "alice"
        bob = "bob"

        import uuid as guid

        model_id = str(guid.uuid4())
        # Generating server
        random_user = "user_" + str(guid.uuid4())
        logging.info("User for test " + random_user)
        docker_api = homeserver.cs_api.replace("localhost", "10.0.2.2")

        login_data = {
            "username": random_user,
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": homeserver.cs_api,
            },
        }

        # maybe factor out the above, maybe not...
        model = Model(
            model_id,
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
        model.calculate_transitions()

        client_one.set_colour(alice)
        client_one.set_model(model)
        client_two.set_colour(bob)
        client_two.set_model(model)
        return model
