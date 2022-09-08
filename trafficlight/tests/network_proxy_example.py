import uuid
from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class SendMessagesTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(SendMessagesTestSuite, self).__init__()
        self.clients_needed = 2
        self.network_proxy = True
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
        client_one = clients[0].name
        client_two = clients[1].name

        # TODO instead of pulling names from clients, just use clients as keys directly in the below...

        # Generating server
        random_user = "user_" + str(uuid.uuid4())

        login_data = {
            "username": random_user,
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": network_proxy.registration.get("url"),
                "local": network_proxy.registration.get("url"),
            },
        }

        # TODO: work out what local_docker should do :|

        network_proxy_name = network_proxy.name

        # maybe factor out the above, maybe not...
        model = Model(
            [
                ModelState(
                    "setup",
                    {
                        network_proxy_name: {
                            "action": "proxyUrl",
                            "data": {"url": servers[0].cs_api},
                            "responses": {"proxyUrlSet": "disable"},
                        },
                    },
                ),
                ModelState(
                    "disable",
                    {
                        network_proxy_name: {
                            "action": "disableEndpoint",
                            "data": {"endpoint": "/_matrix/client/v1/rooms"},
                            "responses": {"endpointDisabled": "login"},
                        },
                    },
                ),
                ModelState(
                    "login",
                    {
                        client_one: {
                            "action": "login",
                            "data": login_data,
                            "responses": {"loggedIn": "enable"},
                        },
                    },
                ),
                ModelState(
                    "enable",
                    {
                        network_proxy_name: {
                            "action": "enableEndpoint",
                            "data": {"endpoint": "/_matrix/client/v1/rooms"},
                            "responses": {"endpointEnabled": "complete"},
                        },
                    },
                ),
                ModelState(
                    "complete",
                    {
                        client_one: {"action": "exit", "responses": {}},
                        client_two: {"action": "exit", "responses": {}},
                        network_proxy_name: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "disable",
        )

        model.calculate_transitions()

        return model
