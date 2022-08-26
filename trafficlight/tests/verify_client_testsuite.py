from typing import List

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects import Client, Model, ModelState
from trafficlight.tests.assertions import assertCompleted, assertEqual


class VerifyClientTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(VerifyClientTestSuite, self).__init__()
        self.clients_needed = 2
        self.servers_needed = 1

    def validate_model(self, model: Model) -> None:
        # NB: Clients do not handle this yet
        assertCompleted(model)

        # NB: Better namespacing should be in place.

        # NB: Alice and Bob are names, yes, but we don't know them in this test.
        # Perhaps get client passed in instead.
        assertEqual(
            model.responses["alice"]["emoji"],
            model.responses["bob"]["emoji"],
            "Emoji accepted should be identical",
        )

    def generate_model(
        self, clients: List[Client], servers: List[HomeserverConfig]
    ) -> Model:
        alice = clients[0].name
        bob = clients[1].name

        homeserver = servers[0]

        # TODO: move into neat user-generation tool
        import uuid as guid

        # Generating server
        random_user = "user_" + str(guid.uuid4())
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

        return model
