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

from trafficlight.homerunner import HomerunnerClient
from trafficlight.objects.adapter import Adapter
from trafficlight.store import add_adapter, get_adapter, get_adapters, get_tests

# Set transitions' log level to INFO; DEBUG messages will be omitted


logger = logging.getLogger(__name__)

# TODO: change this, but we need to provide versioning for clients :|
bp = Blueprint("client", __name__, url_prefix="/client")
homerunner = HomerunnerClient("http://localhost:54321")


async def check_for_new_tests() -> None:
    test_cases = get_tests()
    available_adapters = list(filter(lambda x: x.available(), get_adapters()))
    for test_case in test_cases:
        if test_case.state == "waiting":
            adapters_required = test_case.allocate_adapters(available_adapters)
            if adapters_required is not None:

                logger.info("Starting test %s", test_case)
                await test_case.run(adapters_required, homerunner)
                return
    logger.debug(
        "Not enough client_types to run any test(have %s)",
        [str(item) for item in available_adapters],
    )


@bp.route("/<string:adapter_uuid>/register", methods=["POST"])
async def register(adapter_uuid: str):  # type: ignore

    registration = cast(Dict[str, Any], await request.json)
    logger.info("%s (    ) registered: %s", adapter_uuid, registration)

    existing = get_adapter(adapter_uuid)
    if existing is not None:
        if existing.model is not None:
            raise Exception("Adapter already in use, cannot re-register")
        else:
            logger.info(
                "Adapter re-registered, returning OK again if registration matches"
            )
            return {}
    adapter = Adapter(adapter_uuid, registration)
    add_adapter(adapter)

    current_app.add_background_task(check_for_new_tests)

    return {}


@bp.route("/<string:uuid>/poll", methods=["GET"])
async def poll(uuid: str):  # type: ignore
    adapter = get_adapter(uuid)
    if adapter is None:
        # Very bad situation; client believes it's registered; server has no record
        # do not update server state; tell client to exit and restart with new UUID.
        return {"action": "exit", "responses": []}

    return adapter.poll()


@bp.route("/<string:uuid>/respond", methods=["POST"])
async def respond(uuid: str):  # type: ignore
    adapter = get_adapter(uuid)
    if adapter is None:
        # Again, bad situation; client is doing something and no-one knows why
        raise Exception("Unknown adapter performing update")
    response = await request.json
    update = cast(Dict[str, Any], response)
    adapter.respond(update)

    return {}


@bp.route("/<string:uuid>/error", methods=["POST"])
async def error(uuid: str):  # type: ignore
    adapter = get_adapter(uuid)
    error_json = await request.json
    logger.info(error_json)
    if adapter is None:
        # Again, bad situation; client is doing something and no-one knows why
        # But in this case it's trying to complain, so we should express it in the logs
        logger.info("Got error from ${uuid}, unable to route internally\n${response}")
        raise Exception("Unknown adapter raising error")

    update = cast(Dict[str, Any], error_json)
    # Using the same API format as sentry to capture the error in a reasonable way:
    error_body = update["error"]

    adapter.error(error_body)

    return {}


@bp.route("/<string:uuid>/upload", methods=["POST"])
async def upload(uuid: str):  # type: ignore
    adapter = get_adapter(uuid)

    if adapter is None:
        # Again, bad situation; client is doing something and no-one knows why
        # But in this case it's trying to complain, so we should express it in the logs
        logger.info("Got upload from ${uuid}, unable to route internally")
        raise Exception("Unknown adapter raising error")

    for name, file in (await request.files).items():
        filename = secure_filename(file.filename)
        target = str(current_app.config.get("UPLOAD_FOLDER")) + uuid + filename
        logger.info(f"Uploading file {name} to {target}")
        await file.save(target)
        adapter.upload(filename, target)

    return {}
