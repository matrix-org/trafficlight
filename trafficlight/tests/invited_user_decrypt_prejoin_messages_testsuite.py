import uuid
from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class InviteUserDecryptPrejoinMessagesTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(InviteUserDecryptPrejoinMessagesTestSuite, self).__init__()
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
                            "responses": {"registered": "create_room"},
                        },
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
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "change_history_settings"},
                        }
                    },
                ),
                ModelState(
                    "change_history_settings",
                    {
                        alice: {
                            "action": "change_room_history_visibility",
                            "data": {"historyVisibility": "invited"},
                            "responses": {"changed": "send_message_before_invite"},
                        }
                    },
                ),
                ModelState(
                    "send_message_before_invite",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {
                                "message": "Bob should not be able to read this, as he isn't invited yet"
                            },
                            "responses": {"message_sent": "invite_user"},
                        }
                    },
                ),
                # ModelState(
                #     "register_b",
                #     {
                #         bob: {
                #             "action": "register",
                #             "data": login_data_bob,
                #             "responses": {"registered": "invite_user"},
                #         }
                #     },
                # ),
                ModelState(
                    "invite_user",
                    {
                        alice: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'{login_data_bob["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"invited": "send_message_after_invite"},
                        }
                    },
                ),
                ModelState(
                    "send_message_after_invite",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {
                                "message": "Bob should be able to read this message!"
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
                            "responses": {"accepted": "verify_message_in_timeline"},
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
