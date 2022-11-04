from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class MessageDecryptionAfterStorageClearedTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(MessageDecryptionAfterStorageClearedTestSuite, self).__init__()
        self.clients_needed = 2
        self.servers_needed = 1

    def validate_model(self, model: Model) -> None:
        # NB: Clients do not handle this yet
        assertCompleted(model)

        # NB: Better namespacing should be in place.

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
        docker_api = homeserver.cs_api.replace("localhost", "10.0.2.2")

        login_data_alice = {
            "username": "alice" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,
                "local": homeserver.cs_api,
            },
        }

        login_data_bob = {
            "username": "bob_" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,
                "local": homeserver.cs_api,
            },
        }

        # maybe factor out the above, maybe not...
        model = Model(
            [
                ModelState(
                    "init_a",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data_alice,
                            "responses": {"registered": "init_b"},
                        },
                    },
                ),
                ModelState(
                    "init_b",
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
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "invite_bob"},
                        }
                    },
                ),
                ModelState(
                    "invite_bob",
                    {
                        alice: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'{login_data_bob["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"invited": "bob_accepts_invite"},
                        }
                    },
                ),
                ModelState(
                    "bob_accepts_invite",
                    {
                        bob: {
                            "action": "accept_invite",
                            "responses": {"accepted": "alice_clears_storage"},
                        },
                    },
                ),
                ModelState(
                    "alice_clears_storage",
                    {
                        alice: {
                            "action": "clear_idb_storage",
                            "responses": {"storage_cleared": "alice_reloads_page"},
                        }
                    },
                ),
                ModelState(
                    "alice_reloads_page",
                    {
                        alice: {
                            "action": "reload",
                            "responses": {"reloaded": "bob_sends_message"},
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
                            "responses": {"message_sent": "verify_message_in_timeline"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline",
                    {
                        alice: {
                            "action": "verify_message_in_timeline",
                            "data": {
                                "message": "Alice should be able to read this message!",
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
            "init_a",
        )
        model.calculate_transitions()

        return model