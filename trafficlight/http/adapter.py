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
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, cast

from quart import Blueprint, current_app, request
from werkzeug.utils import secure_filename

from trafficlight.homerunner import HomerunnerClient
from trafficlight.internals.adapter import Adapter
from trafficlight.internals.exceptions import (
    ActionException,
    AdapterException,
    PollTimeoutException,
    RemoteException,
    ShutdownException,
)
from trafficlight.store import (
    add_adapter,
    get_adapter,
    get_adapters,
    get_tests,
    remove_adapter,
)

IDLE_ADAPTER_UNRESPONSIVE_DELAY = timedelta(minutes=1)
ACTIVE_ADAPTER_UNRESPONSIVE_DELAY = timedelta(minutes=3)
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

                async def run() -> None:
                    await test_case.run(adapters_required, homerunner)

                current_app.add_background_task(run)
                return
    logger.debug(
        "Not enough client_types to run any test(have %s)",
        [str(item) for item in available_adapters],
    )


last_cleanup = datetime.now()
stop_background_tasks = False


async def cleanup_unresponsive_adapters() -> None:
    now = datetime.now()
    for adapter in list(get_adapters()):
        if adapter.available():
            # This will remove from the lists and UI pieces; if the adapter does wake up later it will
            # error and be told to exit and restart.
            #
            # This will prevent us from assigning tests to inactive adapters.
            if now - adapter.last_polled > IDLE_ADAPTER_UNRESPONSIVE_DELAY:
                logger.warning(
                    f"Removing adapter {adapter.guid} due to not responding since {adapter.last_polled} (more than {IDLE_ADAPTER_UNRESPONSIVE_DELAY})"
                )
                remove_adapter(adapter)

            pass  # idle out adapters that haven't contacted in last 60s
        elif adapter.completed:
            # Ignore for now... but when we have large numbers of these maybe we should start doing a cleanup
            # process to remove from UI and hash lookups etc.
            pass
        else:
            # This adapter is in use. This timeout will force tests to fail in the face of an adapter that is unresponsive
            # so we can at least make some progress
            # If the adapter ends up responding/polling eventually, it will be told the test has failed and to exit and restart
            # allowing us to continue with other tests
            # This won't repeat as side effect of an error is to move to completed.
            late_poll = now - adapter.last_polled > ACTIVE_ADAPTER_UNRESPONSIVE_DELAY
            late_response = (
                now - adapter.last_responded > ACTIVE_ADAPTER_UNRESPONSIVE_DELAY
            )

            if late_poll and late_response:
                logger.warning(
                    f"Raising error for adapter {adapter.guid} due to not responding since {adapter.last_responded}, and not polling since {adapter.last_polled} (both more than {ACTIVE_ADAPTER_UNRESPONSIVE_DELAY})"
                )
                adapter.error(
                    PollTimeoutException(
                        f"Timed out adapter after {ACTIVE_ADAPTER_UNRESPONSIVE_DELAY}"
                    ),
                    update_last_responded=False,
                )


async def loop_cleanup_unresponsive_adapters() -> None:
    while not stop_background_tasks:
        logging.info("Running sweep for idle adapters")
        await cleanup_unresponsive_adapters()
        await asyncio.sleep(30)

    logging.info("Finished sweep task")


async def loop_check_for_new_tests() -> None:
    while not stop_background_tasks:
        logging.info("Running sweep for new tests")
        await check_for_new_tests()
        await asyncio.sleep(30)
    logging.info("Finished new test task")


async def adapter_shutdown() -> None:
    for adapter in get_adapters():
        adapter.error(ShutdownException("Shutting down trafficlight"))


@bp.route("/<string:adapter_uuid>/register", methods=["POST"])
async def register(adapter_uuid: str):  # type: ignore

    registration = cast(Dict[str, Any], await request.json)
    logger.info("%s (    ) registered: %s", adapter_uuid, registration)

    existing = get_adapter(adapter_uuid)
    if existing is not None:
        if existing.client is not None:
            raise Exception("Adapter already in use, cannot re-register")
        else:
            logger.info(
                "Adapter re-registered, returning OK again if registration matches"
            )
            return {}
    adapter = Adapter(adapter_uuid, registration)
    add_adapter(adapter)
    return {}


@bp.route("/<string:uuid>/poll", methods=["GET"])
async def poll(uuid: str):  # type: ignore
    adapter = get_adapter(uuid)
    poll_response: Dict[str, Any]

    if adapter is None:
        # Very bad situation; client believes it's registered; server has no record
        # do not update server state; tell client to exit and restart with new UUID.
        poll_response = {"action": "exit", "data": {"reason": "no record of this UUID"}}
    else:
        poll_response = adapter.poll()

    logger.info(f"Returning {poll_response} to {uuid}")

    return poll_response


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

    if error_json is None:
        raise Exception("Error request did not include a JSON body")

    update = cast(Dict[str, Any], error_json)

    # Using the same API format as sentry to capture the error in a reasonable way:
    # {
    #    "error": {
    #        "type": "unknown" | "action"
    #        "path": "path/to/error"
    #        "details": "human/details_go_here"
    #    }
    # }
    error_body = update["error"]
    exception: RemoteException
    cause: str
    if adapter.client:
        cause = f"Error from adapter for client {adapter.client.name}"
    else:
        cause = f"Error from adapter {adapter.guid}"
    if error_body["type"] == "action":
        exception = ActionException(
            cause + "\n" + error_body["details"], error_body["path"]
        )
    else:
        exception = AdapterException(
            cause + "\n" + error_body["details"], error_body["path"]
        )

    adapter.error(exception)

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
