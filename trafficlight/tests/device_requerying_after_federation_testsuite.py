from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class DeviceRequeryingAfterFederationTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(DeviceRequeryingAfterFederationTestSuite, self).__init__()
        self.clients_needed = 2
        self.network_proxy_needed = True
        self.servers_needed = 2

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

        homeserver1 = servers[0]
        homeserver2 = servers[0]

        # TODO: move into neat user-generation tool
        import uuid as guid

        proxy_address = network_proxy.registration["endpoint"]
        docker_api = proxy_address.replace("localhost", "10.0.2.2")

        login_data_alice = {
            "username": "alice" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local":homeserver2.cs_api,
            },
        }
        login_data_bob = {
            "username": "bob_" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": homeserver1.cs_api,
            },
        }
        network_proxy_name = network_proxy.name
        # maybe factor out the above, maybe not...
        model = Model(
            [
                ModelState(
                    "create_proxy",
                    {
                        network_proxy_name: {
                            "action": "proxyTo",
                            "data": {
                                "url": homeserver1.cs_api,
                            },
                            "responses": {"proxyToSet": "register_a"},
                        },
                    },
                ),
                ModelState(
                    "register_a",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data_alice,
                            "responses": {"registered": "create_room"},
                        },
                    },
                ),
                ModelState(
                    "create_room",
                    {
                        alice: {
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "register_b"},
                        }
                    },
                ),
                ModelState(
                    "register_b",
                    {
                        bob: {
                            "action": "register",
                            "data": login_data_bob,
                            "responses": {"registered": "invite_user"},
                        },
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
                            "responses": {"accepted": "block_endpoint"},
                        }
                    },
                ),
                ModelState(
                    "block_endpoint",
                    {
                        network_proxy_name: {
                            "action": "disableEndpoint",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sendToDevice",
                            },
                            "responses": {"endpointDisabled": "send_message"},
                        }
                    },
                ),
                ModelState(
                    "send_message",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {"message": "A random message appears!"},
                            "responses": {"message_sent": "wait_for_sendToDevice_1"},
                        }
                    },
                ),
                ModelState(
                    "wait_for_sendToDevice_1",
                    {
                        network_proxy_name: {
                            "action": "waitUntilEndpointAccessed",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sendToDevice",
                            },
                            "responses": {"endpointAccessed": "verify_utd_message"},
                        }
                    },
                ),
                ModelState(
                    "verify_utd_message",
                    {
                        bob: {
                            "action": "verify_last_message_is_utd",
                            "data": {},
                            "responses": {"verified": "enable_endpoint"},
                        }
                    },
                ),
                ModelState(
                    "enable_endpoint",
                    {
                        network_proxy_name: {
                            "action": "enableEndpoint",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sendToDevice",
                            },
                            "responses": {"endpointEnabled": "wait_for_sendToDevice_2"},
                        }
                    },
                ),
                ModelState(
                    "wait_for_sendToDevice_2",
                    {
                        network_proxy_name: {
                            "action": "waitUntilEndpointAccessed",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sendToDevice",
                            },
                            "responses": {"endpointAccessed": "wait_for_decryption"},
                        }
                    },
                ),
                ModelState(
                    "wait_for_decryption",
                    {
                        bob: {
                            "action": "wait",
                            "data": {},
                            "responses": {"wait_over": "verify_message_in_timeline"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline",
                    {
                        bob: {
                            "action": "verify_message_in_timeline",
                            "data": {"message": "A random message appears!"},
                            "responses": {"verified": "complete"},
                        }
                    },
                ),
                ModelState(
                    "complete",
                    {
                        alice: {
                            "action": "exit",
                            "responses": {},
                        },
                        bob: {
                            "action": "exit",
                            "responses": {},
                        },
                    },
                ),
            ],
            "create_proxy",
        )
        model.calculate_transitions()

        return model
