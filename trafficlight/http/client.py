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

from quart import Blueprint, current_app, request
from werkzeug.utils import secure_filename

from trafficlight.objects import Client
from trafficlight.store import add_client, get_client, get_clients, get_tests

# Set transitions' log level to INFO; DEBUG messages will be omitted


logger = logging.getLogger(__name__)

bp = Blueprint("client", __name__, url_prefix="/client")


async def check_for_new_tests() -> None:
    tests = get_tests()
    available_clients = list(filter(lambda x: x.available(), get_clients()))
    for test in tests:
        if test.status == "waiting":
            clients = test.runnable(available_clients)
            if clients is not None:
                logger.info("Starting test %s", test)
                await test.run(clients)
                return
            else:
                logger.info(
                    "Not enough client_types to run test %s (have %s)",
                    test,
                    [str(item) for item in available_clients],
                )


@bp.route("/<string:client_uuid>/register", methods=["POST"])
async def register(client_uuid: str):  # type: ignore

    registration = cast(Dict[str, Any], await request.json)
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

    current_app.add_background_task(check_for_new_tests)

    return {}


@bp.route("/<string:uuid>/poll", methods=["GET"])
async def poll(uuid: str):  # type: ignore
    client = get_client(uuid)
    if client is None:
        # Very bad situation; client belives it's registered; server has no record
        # do not update server state; tell client to exit and restart with new UUID.
        return {"action": "exit", "responses": []}

    return client.poll()


@bp.route("/<string:uuid>/respond", methods=["POST"])
async def respond(uuid: str):  # type: ignore
    client = get_client(uuid)
    if client is None:
        # Again, bad situation; client is doing something and no-one knows why
        raise Exception("Unknown client performing update")
    response = await request.json
    update = cast(Dict[str, Any], response)
    client.respond(update)

    return {}


@bp.route("/<string:uuid>/error", methods=["POST"])
async def error(uuid: str):  # type: ignore
    client = get_client(uuid)
    error_json = await request.json
    logger.info(error_json)
    if client is None:
        # Again, bad situation; client is doing something and no-one knows why
        # But in this case it's trying to complain, so we should express it in the logs
        logger.info("Got error from ${uuid}, unable to route internally\n${response}")
        raise Exception("Unknown client raising error")

    update = cast(Dict[str, Any], error_json)
    # Using the same API format as sentry to capture the error in a reasonable way:
    error_body = update["error"]

    client.error(error_body)

    return {}


@bp.route("/<string:uuid>/upload", methods=["POST"])
async def upload(uuid: str):  # type: ignore
    client = get_client(uuid)

    if client is None:
        # Again, bad situation; client is doing something and no-one knows why
        # But in this case it's trying to complain, so we should express it in the logs
        logger.info("Got upload from ${uuid}, unable to route internally")
        raise Exception("Unknown client raising error")

    for name, file in (await request.files).items():
        filename = secure_filename(file.filename)
        target = str(current_app.config.get("UPLOAD_FOLDER")) + filename
        logger.info(f"Uploading file {name} to {target}")
        await file.save(target)
        client.upload(name, filename)

    return {}
