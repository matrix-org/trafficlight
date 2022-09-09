import uuid
from typing import List

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects import Client, Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class InviteUserDecryptPrejoinMessagesTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(InviteUserDecryptPrejoinMessagesTestSuite, self).__init__()
        self.clients_needed = 1
        self.servers_needed = 1

    def validate_model(self, model: Model) -> None:
        assertCompleted(model)

        # TODO verify the model after completion, eg:
        #        self.assertEqual(model.data["alice_verified_crosssign"]['emoji'],
        #                        model.data["bob_verified_crosssign"]["emoji"],
        #                        "Emoji were not matching")

    def generate_model(
        self, clients: List[Client], servers: List[HomeserverConfig]
    ) -> Model:
        alice = clients[0].name
        #bob = clients[1].name

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
                    "register",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data_alice,
                            "responses": {"registered": "create_room"},
                        },
                        # bob: {
                        #     "action": "register",
                        #     "data": login_data_bob,
                        #     "responses": {"registered": "create_room"},
                        # }
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
                            "responses": {"changed": "complete"},
                        }
                    },
                ),
                ModelState(
                    "send",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {"message": "Bob should not be able to read this, as he isn't invited yet"},
                            "responses": {"message_sent": "complete"},
                        }
                    },
                ),
                
                ModelState(
                    "complete",
                    {
                        alice: {"action": "exit", "responses": {}},
                        #bob: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "register",
        )

        model.calculate_transitions()

        return model
