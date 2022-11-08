from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class TestProxyTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(TestProxyTestSuite, self).__init__()
        self.clients_needed = 3
        self.network_proxy_needed = True
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
        bob_device_1 = clients[1].name
        bob_device_2 = clients[2].name

        homeserver = servers[0]

        # TODO: move into neat user-generation tool
        import uuid as guid

        docker_api = homeserver.cs_api.replace("localhost", "10.0.2.2")

        # Alice will talk to the hs through the proxy
        proxy_address = network_proxy.registration["endpoint"]
        docker_proxy_api = proxy_address.replace("localhost", "10.0.2.2")

        login_data_alice = {
            "username": "alice" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_proxy_api,  # hmm... todo this...
                "local": proxy_address,
            },
        }
        login_data_bob = {
            "username": "bob_" + str(guid.uuid4()),
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": homeserver.cs_api,
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
                                "url": homeserver.cs_api,
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
                            "responses": {"registered": "register_b"},
                        },
                    },
                ),
                ModelState(
                    "register_b",
                    {
                        bob_device_1: {
                            "action": "register",
                            "data": login_data_bob,
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
                        bob_device_1: {
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
                                "endpoint": "/_matrix/client/r0/sync",
                            },
                            "responses": {"endpointDisabled": "bob_login_again"},
                        }
                    },
                ),
                ModelState(
                    "bob_login_again",
                    {
                        bob_device_2: {
                            "action": "login",
                            "data": login_data_bob,
                            "responses": {"loggedin": "bob_opens_room"},
                        }
                    },
                ),
                ModelState(
                    "bob_opens_room",
                    {
                        bob_device_2: {
                            "action": "open-room",
                            "data": {"name": "little test room"},
                            "responses": {"room-opened": "send_message"},
                        }
                    },
                ),
                ModelState(
                    "send_message",
                    {
                        alice: {
                            "action": "send_message",
                            "data": {"message": "A random message appears!"},
                            "responses": {"message_sent": "enable_endpoint"},
                        }
                    },
                ),
                ModelState(
                    "enable_endpoint",
                    {
                        network_proxy_name: {
                            "action": "enableEndpoint",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sync",
                            },
                            "responses": {
                                "endpointEnabled": "Wait_for_keys_to_come_in"
                            },
                        }
                    },
                ),
                ModelState(
                    "Wait_for_keys_to_come_in",
                    {
                        bob_device_2: {
                            "action": "wait",
                            "data": {},
                            "responses": {"wait_over": "verify_message_in_timeline_1"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline_1",
                    {
                        bob_device_1: {
                            "action": "verify_message_in_timeline",
                            "data": {"message": "A random message appears!"},
                            "responses": {"verified": "verify_message_in_timeline_2"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline_2",
                    {
                        bob_device_2: {
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
                        bob_device_1: {
                            "action": "exit",
                            "responses": {},
                        },
                        bob_device_2: {
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
