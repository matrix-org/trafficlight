from typing import List, Optional

import trafficlight.tests
from trafficlight.homerunner import HomeserverConfig
from trafficlight.objects.client import Client
from trafficlight.objects.model import Model, ModelState
from trafficlight.tests.assertions import assertCompleted

# Test Script:
# CLIENT_COUNT=2 REQUIRES_PROXY=true CYPRESS_BASE_URL="https://develop.element.io" ./trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server


class VerifyClientOrderTestSuite(trafficlight.tests.TestSuite):
    def __init__(self) -> None:
        super(VerifyClientOrderTestSuite, self).__init__()
        self.clients_needed = 2
        self.servers_needed = 1
        self.network_proxy_needed = True

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

        homeserver = servers[0]

        # TODO: move into neat user-generation tool
        import uuid as guid

        # Generating server
        random_user = "user_" + str(guid.uuid4())

        proxy_address = network_proxy.registration["endpoint"]
        docker_api = proxy_address.replace("localhost", "10.0.2.2")

        login_data = {
            "username": random_user,
            "password": "bubblebobblebabble",
            "homeserver_url": {
                "local_docker": docker_api,  # hmm... todo this...
                "local": proxy_address,
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
                            "responses": {"proxyToSet": "init_r"},
                        },
                    },
                ),
                ModelState(
                    "init_r",
                    {
                        alice: {
                            "action": "register",
                            "data": login_data,
                            "responses": {"registered": "init_g"},
                        },
                    },
                ),
                ModelState(
                    "init_g",
                    {
                        bob: {
                            "action": "login",
                            "data": login_data,
                            "responses": {"loggedin": "delay_endpoint"},
                        }
                    },
                ),
                ModelState(
                    "delay_endpoint",
                    {
                        network_proxy_name: {
                            "action": "delayEndpoint",
                            "data": {
                                "endpoint": "/_matrix/client/r0/sendToDevice/m.key.verification.ready",
                                "delay": "30000",
                            },
                            "responses": {"endpointDelayed": "start_crosssign"},
                        }
                    },
                ),
                ModelState(
                    "start_crosssign",
                    {
                        bob: {
                            "action": "start_crosssign",
                            "responses": {"started_crosssign": "accept_crosssign"},
                        }
                    },
                ),
                ModelState(
                    "accept_crosssign",
                    {
                        alice: {
                            "action": "accept_crosssign",
                            "responses": {"accepted_crosssign": "verify_crosssign_rg"},
                        }
                    },
                ),
                ModelState(
                    "verify_crosssign_rg",
                    {
                        alice: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "verify_crosssign_g"},
                        },
                        bob: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "verify_crosssign_r"},
                        },
                    },
                ),
                ModelState(
                    "verify_crosssign_r",
                    {
                        alice: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "complete"},
                        }
                    },
                ),
                ModelState(
                    "verify_crosssign_g",
                    {
                        bob: {
                            "action": "verify_crosssign_emoji",
                            "responses": {"verified_crosssign": "complete"},
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
            "create_proxy",
        )
        model.calculate_transitions()

        return model
