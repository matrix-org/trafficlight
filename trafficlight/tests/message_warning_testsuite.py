import uuid
from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class MessageWarningTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(MessageWarningTestSuite, self).__init__()
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
                            "responses": {"registered": "bob_enables_key_backup"},
                        }
                    },
                ),
                ModelState(
                    "bob_enables_key_backup",
                    {
                        bob: {
                            "action": "enable_key_backup",
                            "data": {
                                "key_backup_passphrase": "helloworld123helloworld"
                            },
                            "responses": {"key_backup_enabled": "alice_creates_room"},
                        }
                    },
                ),
                ModelState(
                    "alice_creates_room",
                    {
                        alice: {
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "invite_user"},
                        }
                    },
                ),
                ModelState(
                    "invite_user",
                    {
                        alice: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'{login_data_bob["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"invited": "accept_invite"},
                        }
                    },
                ),
                ModelState(
                    "accept_invite",
                    {
                        bob: {
                            "action": "accept_invite",
                            "responses": {"accepted": "alice_sends_message"},
                        }
                    },
                ),
                ModelState(
                    "alice_sends_message",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {
                                "message": "Bob should be able to read this message!"
                            },
                            "responses": {"message_sent": "bob_logs_out"},
                        }
                    },
                ),
                ModelState(
                    "bob_logs_out",
                    {
                        bob: {
                            "action": "logout",
                            "data": {},
                            "responses": {"logged_out": "bob_login_again"},
                        }
                    },
                ),
                ModelState(
                    "bob_login_again",
                    {
                        bob: {
                            "action": "login",
                            "data": {
                                **login_data_bob,
                                "key_backup_passphrase": "helloworld123helloworld",
                            },
                            "responses": {"loggedin": "bob_opens_room"},
                        }
                    },
                ),
                ModelState(
                    "bob_opens_room",
                    {
                        bob: {
                            "action": "open-room",
                            "data": {"name": "little test room"},
                            "responses": {"room-opened": "verify_message_in_timeline"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline",
                    {
                        bob: {
                            "action": "verify_message_in_timeline",
                            "data": {
                                "message": "Bob should be able to read this message!"
                            },
                            "responses": {"verified": "verify_last_message_is_trusted"},
                        }
                    },
                ),
                ModelState(
                    "verify_last_message_is_trusted",
                    {
                        bob: {
                            "action": "verify_last_message_is_trusted",
                            "data": {},
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
