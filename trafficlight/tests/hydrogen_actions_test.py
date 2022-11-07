from typing import List, Optional

# import uuid
import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted


class HydrogenActionsTest(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(HydrogenActionsTest, self).__init__()
        self.clients_needed = 1
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
        # client_element = clients[1].name

        # TODO instead of pulling names from clients, just use clients as keys directly in the below...

        # Generating server
        docker_api = servers[0].cs_api.replace("localhost", "10.0.2.2")

        login_data = {
            "username": "testuser",
            "password": "complement_meets_min_pasword_req_testuser",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": servers[0].cs_api,
            },
        }

        # login_data_element = {
        #     "username": "alice_" + str(uuid.uuid4()),
        #     "password": "bubblebobblebabble",
        #     "homeserver_url": {
        #         "local_docker": docker_api,  # hmm... todo this...
        #         "local": servers[0].cs_api,
        #     },
        # }

        # maybe factor out the above, maybe not...
        model = Model(
            [
                ModelState(
                    "init_r",
                    {
                        client_one: {
                            "action": "login",
                            "data": login_data,
                            "responses": {"loggedin": "create-room"},
                        },
                    },
                ),
                ModelState(
                    "create-room",
                    {
                        client_one: {
                            "action": "create_room",
                            "data": {"name": "little test room"},
                            "responses": {"room_created": "send_message"},
                        }
                    },
                ),
                ModelState(
                    "send_message",
                    {
                        client_one: {
                            "action": "send_message",
                            "data": {
                                "message": "hello world!"
                            },
                            "responses": {"message_sent": "create-room-2"},
                        }
                    },
                ),
                # ModelState(
                #     "enable_dehydrated_device",
                #     {
                #         client_one: {
                #             "action": "enable_dehydrated_device",
                #             "data": {
                #                 "key_backup_passphrase": "helloworld123"
                #             },
                #             "responses": {"enabled_dehydrated_device": "logout"},
                #         }
                #     },
                # ),
                ModelState(
                    "create-room-2",
                    {
                        client_one: {
                            "action": "create_room",
                            "data": {"name": "little test room 2"},
                            "responses": {"room_created": "open-room"},
                        }
                    },
                ),
                ModelState(
                    "open-room",
                    {
                        client_one: {
                            "action": "open_room",
                            "data": {"name": "little test room"},
                            "responses": {"room-opened": "wait-test"},
                        }
                    },
                ),
                ModelState(
                    "wait-test",
                    {
                        client_one: {
                            "action": "wait",
                            "data": {"time": "2000"},
                            "responses": {"wait_over": "page_reloaded"},
                        }
                    },
                ),
                ModelState(
                    "page_reloaded",
                    {
                        client_one: {
                            "action": "reload",
                            "data": {},
                            "responses": {"reloaded": "verify_message_in_timeline"},
                        }
                    },
                ),
                ModelState(
                    "verify_message_in_timeline",
                    {
                        client_one: {
                            "action": "verify_message_in_timeline",
                            "data": {
                                "message": "hello world!"
                            },
                            "responses": {"verified": "logout"},
                        }
                    },
                ),
                # ModelState(
                #     "register_a",
                #     {
                #         client_element: {
                #             "action": "register",
                #             "data": login_data_element,
                #             "responses": {"registered": "create_room_element"},
                #         }
                #     },
                # ),
                # ModelState(
                #     "create_room_element",
                #     {
                #         client_element: {
                #             "action": "create_room",
                #             "data": {"name": "little test room"},
                #             "responses": {"room_created": "invite_user"},
                #         }
                #     },
                # ),
                # ModelState(
                #     "invite_user",
                #     {
                #         client_element: {
                #             "action": "invite_user",
                #             "data": {
                #                 "userId": f'{login_data["username"]}:{servers[0].server_name}'
                #             },
                #             "responses": {"invited": "accept_invite"},
                #         }
                #     },
                # ),
                # ModelState(
                #     "accept_invite",
                #     {
                #         client_one: {
                #             "action": "accept_invite",
                #             "responses": {"accepted": "logout"},
                #         }
                #     },
                # ),
                ModelState(
                    "logout",
                    {
                        client_one: {
                            "action": "logout",
                            "data": {},
                            "responses": {"logged_out": "second_login"},
                        }
                    },
                ),
                ModelState(
                    "second_login",
                    {
                        client_one: {
                            "action": "login",
                            "data": login_data,
                            "responses": {"loggedin": "open-room-again"},
                        },
                    },
                ),
                ModelState(
                    "open-room-again",
                    {
                        client_one: {
                            "action": "open_room",
                            "data": {"name": "little test room"},
                            "responses": {"room-opened": "verify_utd_message"},
                        }
                    },
                ),
                ModelState(
                    "verify_utd_message",
                    {
                        client_one: {
                            "action": "verify_last_message_is_utd",
                            "data": {},
                            "responses": {"verified": "clear_storage"},
                        }
                    },
                ),
                ModelState(
                    "clear_storage",
                    {
                        client_one: {
                            "action": "clear_idb_storage",
                            "data": {},
                            "responses": {"storage_cleared": "complete"},
                        }
                    },
                ),
                ModelState(
                    "complete",
                    {
                        client_one: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "init_r",
        )

        model.calculate_transitions()

        return model
