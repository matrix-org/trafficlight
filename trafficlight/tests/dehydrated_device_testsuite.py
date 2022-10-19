import uuid
from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class DehydatedDeviceTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(DehydatedDeviceTestSuite, self).__init__()
        self.clients_needed = 2
        self.servers_needed = 1

    def validate_model(self, model: Model) -> None:
        assertCompleted(model)

        # TODO verify the model after completion, eg:
        #        self.assertEqual(model.data["alice_verified_crosssign"]['emoji'],
        #                        model.data["bob_verified_crosssign"]["emoji"],
        #                        "Emoji were not matching")

    def generate_model(
        self,
        clients: List[Client],
        servers: List[HomeserverConfig],
        network_proxy: Optional[Client],
    ) -> Model:
        alice = clients[0].name
        bob = clients[1].name

        # TODO instead of pulling names from clients, just use clients as keys directly in the below...

        # Generating server
        docker_api = servers[0].cs_api.replace("localhost", "10.0.2.2")

        login_data_alice = {
            "username": "alice_" + str(uuid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": servers[0].cs_api,
            },
        }

        login_data_bob = {
            "username": "bob_" + str(uuid.uuid4()),
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
                    "register_a",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data_alice,
                            "responses": {"registered": "register_b"},
                        },
                    },
                ),
                ModelState(
                    "register_b",
                    {
                        bob: {
                            "action": "register",
                            "data": login_data_bob,
                            "responses": {"registered": "enable_dehydrated_device"},
                        }
                    },
                ),
                ModelState(
                    "enable_dehydrated_device",
                    {
                        alice: {
                            "action": "enable_dehydrated_device",
                            "data": {},
                            "responses": {"enabled_dehydrated_device": "create_room"},
                        }
                    },
                ),
                ModelState(
                    "create_room",
                    {
                        bob: {
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "invite_user"},
                        }
                    },
                ),
                ModelState(
                    "invite_user",
                    {
                        bob: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'{login_data_alice["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"invited": "accept_invite"},
                        }
                    },
                ),
                ModelState(
                    "accept_invite",
                    {
                        alice: {
                            "action": "accept_invite",
                            # "data": {"message": "Bob should be able to read this message!"},
                            "responses": {"accepted": "alice_logs_out"},
                        }
                    },
                ),
                ModelState(
                    "alice_logs_out",
                    {
                        alice: {
                            "action": "logout",
                            "data": {},
                            "responses": {"logged_out": "bob_advances_time"},
                        }
                    },
                ),
                ModelState(
                    "bob_advances_time",
                    {
                        bob: {
                            "action": "advance_clock",
                            "data": {"milliseconds": 1209600000},
                            "responses": {"advanced_clock": "bob_sends_message"},
                        }
                    },
                ),
                ModelState(
                    "bob_sends_message",
                    {
                        bob: {
                            "action": "send_message",
                            "data": {
                                "message": "Alice should be able to read this message!"
                            },
                            "responses": {"message_sent": "alice_login_again"},
                        }
                    },
                ),
                ModelState(
                    "alice_login_again",
                    {
                        alice: {
                            "action": "login",
                            "data": {
                                **login_data_alice,
                                "key_backup_passphrase": "helloworld123helloworld",
                            },
                            "responses": {"loggedin": "alice_opens_room"},
                        }
                    },
                ),
                ModelState(
                    "alice_opens_room",
                    {
                        alice: {
                            "action": "open-room",
                            "data": {"name": "little test room"},
                            "responses": {"room-opened": "verify_message_in_timeline"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline",
                    {
                        alice: {
                            "action": "verify_message_in_timeline",
                            "data": {
                                "message": "Alice should be able to read this message!"
                            },
                            "responses": {"verified": "complete"},
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
            "register_a",
        )

        model.calculate_transitions()

        return model
