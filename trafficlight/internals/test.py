from itertools import product
from typing import Dict, List, Optional

from trafficlight.client_types import ClientType, NetworkProxy
from trafficlight.internals.testcase import TestCase
from trafficlight.server_types import ServerType


class Test(object):
    """
    Extend Test to provide a test case.

    It is required to implement configure() and declare()

    The folow will be:

    __init__(self, configure: TestInit) -> Initial setup of test completes; this locks in the server types and client
    types defined in the configuration. The result is a Test that knows what it needs before it can run.

    The test will then continue initilization by identifying the test cases required from itself.
    """

    def __init__(self):
        self.server_type: Optional[ServerType] = None
        self.server_names: List[str] = []
        self.clients: Dict[str, List[ClientType]] = {}

    def __str__(self):
        return f"{self.name()}"

    def name(self):
        return self.__class__.__name__

    def _server_under_test(self, server_type: ServerType, names: List[str]):
        self.server_type = server_type
        self.server_names = names

    def _client_under_test(self, client_types: List[ClientType], name: str):
        self.clients[name] = client_types

    def _network_proxy(self, name: str):
        self.clients[name] = [NetworkProxy()]

    def generate_test_cases(self) -> List[TestCase]:
        test_cases: List[TestCase] = []

        client_var_names = list(self.clients.keys())

        all_client_types: List[List[ClientType]] = []

        for client_var_name in client_var_names:
            all_client_types.append(self.clients[client_var_name])

        client_type_product = list(product(*all_client_types))

        for client_types in client_type_product:

            remapped_client_types = {}
            for i in range(0, len(client_var_names)):
                remapped_client_types[client_var_names[i]] = client_types[i]

            test_cases.append(
                TestCase(
                    self,
                    self.server_type,
                    self.server_names,
                    remapped_client_types,
                )
            )

        return test_cases
