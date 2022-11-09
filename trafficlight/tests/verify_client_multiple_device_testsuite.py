from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class VerifyClientMultipleDeviceTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(VerifyClientMultipleDeviceTestSuite, self).__init__()
        self.clients_needed = 2
        self.servers_needed = 1

    def validate_model(self, model: Model) -> None:
        # NB: Clients do not handle this yet
        assertCompleted(model)

        # NB: Better namespacing should be in place.

        # NB: Alice and Bob are names, yes, but we don't know them in this test.
        # Perhaps get client passed in instead.

    def generate_model(
        self,
        clients: List[Client],
        servers: List[HomeserverConfig],
        network_proxy: Optional[Client],
    ) -> Model:
        alice = clients[0].name
        bob = clients[1].name

        homeserver = servers[0]

        # TODO: move into neat user-generation tool
        import uuid as guid

        # Generating server
        random_user = "user_" + str(guid.uuid4())
        docker_api = homeserver.cs_api.replace("localhost", "10.0.2.2")

        login_data_alice = {
            "username": random_user,
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": homeserver.cs_api,
            },
        }

        login_data_bob = {
            "username": "bob_" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": servers[0].cs_api,
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
                            "data": login_data_alice,
                            "responses": {"registered": "init_g"},
                        },
                    },
                ),
                ModelState(
                    "init_g",
                    {
                        bob: {
                            "action": "register",
                            "data": login_data_bob,
                            "responses": {"registered": "create_room"},
                        }
                    },
                ),
                ModelState(
                    "create_room",
                    {
                        alice: {
                            "action": "create_dm",
                            "data": {
                                "userId": f'{login_data_bob["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"dm_created": "send_message"},
                        }
                    },
                ),
                ModelState(
                    "send_message",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {
                                "message": "Bob should not be able to read this, as he isn't invited yet"
                            },
                            "responses": {"message_sent": "accept_invite"},
                        }
                    },
                ),
                ModelState(
                    "accept_invite",
                    {
                        bob: {
                            "action": "accept_invite",
                            # "data": {"message": "Bob should be able to read this message!"},
                            "responses": {"accepted": "start_crosssign"},
                        }
                    },
                ),
                ModelState(
                    "start_crosssign",
                    {
                        bob: {
                            "action": "start_crosssign",
                            "data": {
                                "userId": f'{login_data_alice["username"]}:{servers[0].server_name}'
                            },
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
