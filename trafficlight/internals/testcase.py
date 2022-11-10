import logging
from typing import Dict, List, Optional

from trafficlight.client_types import ClientType
from trafficlight.homerunner import HomerunnerClient, HomeServer
from trafficlight.internals.client import Client
from trafficlight.objects.adapter import Adapter
from trafficlight.server_types import ServerType

logger = logging.getLogger(__name__)


class TestCase:
    def __init__(
        self,
        guid: str,
        test,
        server_type: ServerType,
        server_names: List[str],
        client_types: Dict[str, ClientType],
    ) -> None:
        self.last_exception = None
        self.guid = guid
        self.client_types = client_types
        self.server_type = server_type
        self.server_names = server_names
        self.test = test
        self.state = "waiting"
        self.servers: List[HomeServer] = []
        self.files: Dict[str, str] = {}

    def __repr__(self):
        return f"{self.test.name()} ({self.server_type} {self.client_types})"

    def allocate_adapters(
        self, available_adapters: List[Adapter]
    ) -> Optional[Dict[str, Adapter]]:
        """
        Return None if not enough adapters are found, otherwise return list of adapters i need
        @param available_adapters:
        @return:
        """
        remaining_adapters = list(available_adapters)
        used_adapters: Dict[str, Adapter] = {}
        for (client_var_name, client_type) in self.client_types.items():
            for adapter in remaining_adapters:
                if client_type.match(adapter):
                    remaining_adapters.remove(adapter)
                    used_adapters[client_var_name] = adapter
                    break
            else:
                return None
        return used_adapters

    async def run(self, adapters: Dict[str, Adapter], homerunner: HomerunnerClient):

        # turn adapters into clients
        kwargs = {}
        for (client_var_name, adapter) in adapters.items():
            client = Client(f"{self.test.name()} {client_var_name}", self)
            adapter.set_client(client)
            kwargs[client_var_name] = client

        homeservers = await self.server_type.create(self.guid, homerunner)
        for i in range(0, self.server_names):
            kwargs[self.server_names[i]] = homeservers[i]

        # This may well bail out entirely if the configuration of the test is incorrect
        # But this is a badly written test so is actually OK.
        try:
            logger.info(f"Test setup. Beginning run with kwargs {kwargs}")
            await self.test.run(**kwargs)  # type: ignore
            self.state = "done"
        except Exception as e:
            self.state = "failed"
            self.last_exception = e
            logger.exception(e)
        finally:
            for adapter in adapters.values():
                adapter.finished()
            for server in self.servers:
                server.finished()
