import uuid
from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted

# Test Command:
# CLIENT_COUNT=2 CYPRESS_BASE_URL="https://develop.element.io" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server


class KeyRestoreMarksSessionAsVerifiedTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(KeyRestoreMarksSessionAsVerifiedTestSuite, self).__init__()
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
        alice_1 = clients[0].name
        alice_2 = clients[1].name

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

        # maybe factor out the above, maybe not...
        model = Model(
            [
                ModelState(
                    "register_a",
                    {
                        alice_1: {
                            "action": "register",
                            "data": login_data_alice,
                            "responses": {"registered": "alice_enables_key_backup"},
                        },
                    },
                ),
                ModelState(
                    "alice_enables_key_backup",
                    {
                        alice_1: {
                            "action": "enable_key_backup",
                            "data": {
                                "key_backup_passphrase": "helloworld123helloworld"
                            },
                            "responses": {"key_backup_enabled": "login_a"},
                        }
                    },
                ),
                ModelState(
                    "login_a",
                    {
                        alice_2: {
                            "action": "login",
                            "data": {
                                **login_data_alice,
                                "key_backup_passphrase": "helloworld123helloworld",
                            },
                            "responses": {"loggedin": "verify_device_is_trusted"},
                        }
                    },
                ),
                ModelState(
                    "verify_device_is_trusted",
                    {
                        alice_1: {
                            "action": "verify_trusted_device",
                            "responses": {"verified": "complete"},
                        }
                    },
                ),
                ModelState(
                    "complete",
                    {
                        alice_1: {"action": "exit", "responses": {}},
                        alice_2: {"action": "exit", "responses": {}},
                    },
                ),
            ],
            "register_a",
        )

        model.calculate_transitions()

        return model
