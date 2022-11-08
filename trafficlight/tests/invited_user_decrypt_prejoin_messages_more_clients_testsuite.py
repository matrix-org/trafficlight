import uuid
from typing import Any, Dict, List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted

# Test Script:
# CLIENT_COUNT=2 HYDROGEN_COUNT=8 CYPRESS_BASE_URL="https://develop.element.io" HYDROGEN_APP_URL="http://localhost:3000" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server


class InviteUserDecryptPrejoinMessagesMoreClientsTestSuite(
    trafficlight.tests.TestSuite
):
    def __init__(self) -> None:
        super(InviteUserDecryptPrejoinMessagesMoreClientsTestSuite, self).__init__()
        self.clients_needed = 10
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
        elementClients = list(filter(lambda c: c.registration["type"] == "element-web", clients))
        hydrogenClients = list(filter(lambda c: c.registration["type"] == "hydrogen-web", clients))
        alice = elementClients[0].name
        bob = elementClients[1].name

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

        login_model_states = []
        invite_model_states = []
        accept_invite_states = []
        verify_message_states = []

        # Alice and Bob are treated separately!
        additional_clients_needed = self.clients_needed - 2
        for i in range(additional_clients_needed):
            login_model_states.append(
                ModelState(
                    f"login_{i}",
                    {
                        hydrogenClients[i].name: {
                            "action": "login",
                            "data": generate_login_data(servers[0].cs_api, f"testuser{i+1}"),
                            "responses": {
                                "loggedin": "invite_user" if i == additional_clients_needed - 1 else f"login_{i+1}"
                            },
                        }
                    },
                )
            )

            invite_model_states.append(
                ModelState(
                    f"invite_{i}",
                    {
                        alice: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'testuser{i+1}:{servers[0].server_name}',
                            },
                            "responses": {
                                "invited": "accept_invite" if i == additional_clients_needed - 1 else f"invite_{i+1}"
                            },
                        }
                    },
                )
            )

            accept_invite_states.append(
                ModelState(
                    f"accept_invite_{i}",
                    {
                        hydrogenClients[i].name: {
                            "action": "accept_invite",
                            "data": {},
                            "responses": {
                                "accepted": "verify_message_in_timeline" if i == additional_clients_needed - 1 else f"accept_invite_{i+1}"
                            },
                        }
                    },
                )
            )

            verify_message_states.append(
                ModelState(
                    f"verify_message_utd_{i}",
                    {
                        hydrogenClients[i].name: {
                            "action": "verify_last_message_is_utd",
                            "data": {},
                            "responses": {
                                "verified": "complete" if i == additional_clients_needed - 1 else f"verify_message_utd_{i+1}"
                            },
                        }
                    },
                )
            )
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
                            "responses": {"message_sent": "register_b"},
                        }
                    },
                ),
                ModelState(
                    "register_b",
                    {
                        bob: {
                            "action": "register",
                            "data": login_data_bob,
                            "responses": {"registered": "login_0"},
                        }
                    },
                ),
                *login_model_states,
                ModelState(
                    "invite_user",
                    {
                        alice: {
                            "action": "invite_user",
                            "data": {
                                "userId": f'{login_data_bob["username"]}:{servers[0].server_name}'
                            },
                            "responses": {"invited": "invite_0"},
                        }
                    },
                ),
                *invite_model_states,
                ModelState(
                    "accept_invite",
                    {
                        bob: {
                            "action": "accept_invite",
                            # "data": {"message": "Bob should be able to read this message!"},
                            "responses": {"accepted": "send_message_after_invite"},
                        }
                    },
                ),
                ModelState(
                    "send_message_after_invite",
                    {
                        bob: {
                            "action": "send_message",
                            "data": {
                                "message": "Everybody should be able to read this message!"
                            },
                            "responses": {"message_sent": "accept_invite_0"},
                        }
                    },
                ),
                *accept_invite_states,
                ModelState(
                    "verify_message_in_timeline",
                    {
                        bob: {
                            "action": "verify_message_in_timeline",
                            "data": {
                                "message": "Everybody should be able to read this message!"
                            },
                            "responses": {"verified": "verify_message_utd_0"},
                        }
                    },
                ),
                *verify_message_states,
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


def generate_login_data(cs_api: str, username: str) -> Dict[str, Any]:
    docker_api = cs_api.replace("localhost", "10.0.2.2")
    return {
        "username": username,
        "password": "complement_meets_min_pasword_req_" + username,
        "homeserver_url": {
            "local_docker": docker_api,  # hmm... todo this...
            "local": cs_api,
        },
    }
