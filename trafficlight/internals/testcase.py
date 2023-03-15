import hashlib
import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from quart import current_app

from trafficlight.client_types import ClientType
from trafficlight.homerunner import HomerunnerClient, HomeServer
from trafficlight.internals.adapter import Adapter
from trafficlight.internals.client import MatrixClient, NetworkProxyClient
from trafficlight.internals.exceptions import ActionException, AdapterException
from trafficlight.server_types import ServerType

logger = logging.getLogger(__name__)


class TestCase:
    def __init__(
        self,
        test: Any,
        server_type: ServerType,
        server_names: List[str],
        client_types: Dict[str, ClientType],
    ) -> None:
        self.exceptions: List[str] = []
        self.guid = hashlib.md5(
            f"TestCase{test.name()}{server_type.name()}{server_names}{client_types}".encode(
                "utf-8"
            )
        ).hexdigest()
        self.client_types = client_types
        self.server_type = server_type
        self.server_names = server_names
        self.test = test
        self.state = "waiting"
        self.servers: List[HomeServer] = []
        self.files: Dict[str, str] = {}
        self.adapters: Optional[Dict[str, Adapter]] = None

    def __repr__(self) -> str:
        return f"{self.test.name()} ({self.server_type} {self.client_types})"

    def description(self) -> str:
        return f"{self.server_type} {self.client_types}"

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

    async def run(
        self, adapters: Dict[str, Adapter], homerunner: HomerunnerClient
    ) -> None:
        self.state = "preparing"
        self.adapters = adapters
        # turn adapters into clients
        kwargs: Dict[str, Union[HomeServer, MatrixClient, NetworkProxyClient]] = {}

        for (client_var_name, adapter) in adapters.items():
            client: Union[MatrixClient, NetworkProxyClient]
            if adapter.registration["type"] == "network-proxy":
                client = NetworkProxyClient(client_var_name, self, adapter.registration)
            else:
                client = MatrixClient(client_var_name, self, adapter.registration)
            adapter.set_client(client)
            kwargs[client_var_name] = client

        homeservers = await homerunner.create(self.guid, self.server_type)
        for i in range(0, len(self.server_names)):
            kwargs[self.server_names[i]] = homeservers[i]

        # This may well bail out entirely if the configuration of the test is incorrect
        # But this is a badly written test so is actually OK.
        try:
            logger.info(f"Test setup. Beginning run with kwargs {kwargs}")
            self.state = "running"
            await self.test.run(**kwargs)
            self.state = "success"
        except AssertionError:
            # Treating a test that throws an assertionError as a failure
            self.state = "failed"
            self.exceptions.append("".join(traceback.format_exc()))
        except ActionException as e:
            # Treating an adapter that fails to perform an action as a failure
            self.state = "failed"
            self.exceptions.append(e.formatted_message)
        except AdapterException as e:
            # Treating an adapter that causes another type of exception as an error
            self.state = "error"
            self.exceptions.append(e.formatted_message)
        except Exception:
            # Treating everything else as an error as well... eg compilation failures
            self.state = "error"
            self.exceptions.append("".join(traceback.format_exc()))
        finally:
            for adapter in adapters.values():
                adapter.finished()
            for server in self.servers:
                server.finished()
            if current_app().kiwi_client:
                current_app().kiwi_client.

