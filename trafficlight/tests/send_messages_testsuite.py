import uuid
from typing import List

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class SendMessagesTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(SendMessagesTestSuite, self).__init__()
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
        client_one = clients[0].name

        # TODO instead of pulling names from clients, just use clients as keys directly in the below...

        # Generating server
        random_user = "user_" + str(uuid.uuid4())
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
            [
                ModelState(
                    "init_r",
                    {
                        client_one: {
                            "action": "register",
                            "data": login_data,
                            "responses": {"registered": "create_room"},
                        },
                    },
                ),
                ModelState(
                    "create_room",
                    {
                        client_one: {
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "send"},
                        }
                    },
                ),
                ModelState(
                    "send",
                    {
                        client_one: {
                            "action": "send_message",
                            "data": {"message": "hi there!"},
                            "responses": {"message_sent": "complete"},
                        }
                    },
                ),
                ModelState(
                    "complete",
                    {
                        client_one: {"action": "exit", "responses": {}},
                        #client_two: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "init_r",
        )

        model.calculate_transitions()

        return model
