# vim: expandtab ts=4:
# Copyright 2022 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from typing import Any, Dict, cast

from flask import Blueprint, request, typing

from trafficlight.store import add_client, get_client, get_clients, get_tests
from trafficlight.objects import Client
logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted

logging.getLogger("transitions").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


bp = Blueprint("client", __name__, url_prefix="/client")


@bp.route("/<string:client_uuid>/register", methods=["POST"])
def register(client_uuid: str) -> typing.ResponseValue:
    registration = cast(Dict[str, Any], request.json)
    logger.info("%s (    ) registered: %s", client_uuid, registration)

    existing = get_client(client_uuid)
    if existing is not None:
        if existing.model is not None:
            raise Exception("Client already in use")
        else:
            logger.info(
                "Client re-registered, returning OK again if registration matches"
            )
            return {}
    client = Client(client_uuid, registration)
    add_client(client)

    tests = get_tests()
    available_clients = list(filter(lambda x: x.model is None, get_clients()))
    for test in tests:
        if test.status == "waiting":
            clients = test.runnable(available_clients)
            if clients is not None:
                logger.info("Running test %s", test)
                test.run(clients)
                return {}
            else:
                logger.info(
                    "Not enough client_types to run test %s (have %s)",
                    test,
                    [str(item) for item in available_clients],
                )
    return {}


@bp.route("/<string:uuid>/poll", methods=["GET"])
def poll(uuid: str) -> typing.ResponseValue:
    client = get_client(uuid)
    if client is None:
        # Very bad situation; client belives it's registered; server has no record
        # do not update server state; tell client to exit and restart with new UUID.
        return {"action": "exit", "responses": []}

    return client.poll()


@bp.route("/<string:uuid>/respond", methods=["POST"])
def respond(uuid: str) -> typing.ResponseValue:
    client = get_client(uuid)
    if client is None:
        # Again, bad situation; client is doing something and no-one knows why
        raise Exception("Unknown client performing update")
    update = cast(Dict[str, Any], request.json)
    client.respond(update)

    return {}
