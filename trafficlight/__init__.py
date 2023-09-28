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
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from quart import Quart

import trafficlight.kiwi as kiwi
from trafficlight.homerunner import HomerunnerClient
from trafficlight.http.adapter import (
    adapter_shutdown,
    loop_check_for_new_tests,
    loop_cleanup_unresponsive_adapters,
    loop_check_all_tests_done,
)
from trafficlight.internals.testsuite import TestSuite
from trafficlight.store import add_testsuite, get_testsuites
from trafficlight.tests import load_tests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


# Format in "2 hours" / "2 minutes" etc.
def format_delaytime(value: datetime) -> str:
    if value is None:
        return "N/A"
    now = datetime.now()
    interval = now - value
    return "%s min %s sec ago" % (
        interval // timedelta(minutes=1),
        int((interval % timedelta(minutes=1)).total_seconds()),
    )


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Quart:
    app = Quart(__name__, instance_relative_config=True)

    # Defaults here:
    app.config.update(
        {
            "TEST_PATTERN": "/**/*_test.py",
            "UPLOAD_FOLDER": "/tmp/",
            "HOMERUNNER_URL": "http://localhost:4090",
            "SERVER_OVERRIDES": {},
            "KIWI_REPORT": False,
            "KIWI_VERBOSE": True,
        }
    )

    # Load configuration from JSON file
    app.config.from_file("trafficlight.json", json.load)

    # TODO: ensure uploads folder is available
    # can i create README.md in there with a comment, for instance...

    # ensure the instance folder exists
    print(f"Test Pattern: {app.config.get('TEST_PATTERN')}")
    print(f"Upload Folder: {app.config.get('UPLOAD_FOLDER')}")
    print(f"Overrides: {app.config.get('SERVER_OVERRIDES')}")
    print(
        f"Kiwi: {app.config.get('KIWI_REPORT')}, Verbose: {app.config.get('KIWI_VERBOSE')}, Product Name: {app.config.get('KIWI_PRODUCT_NAME')}, Product Version: {app.config.get('KIWI_PRODUCT_VERSION')}"
    )

    loaded_tests = load_tests(
        app.config.get("TEST_PATTERN"),
    )
    for test in loaded_tests:
        logger.info(f"Generating test cases for {test.name()}")
        test_cases = test.generate_test_cases()
        for test_case in test_cases:
            logger.info(f" - {test_case}")

        test_suite = TestSuite(test, test_cases)
        add_testsuite(test_suite)

    if app.config.get("KIWI_REPORT"):
        kiwi.kiwi_client = kiwi.KiwiClient(app.config.get("KIWI_VERBOSE"))
        # Screaming quietly for now; i don't want to have more ways to set config options
        # so avoiding env vars coming in from the environment and overriding them from the app configuration.
        # Potentially this is a sign we're not using this API correctly.
        os.environ["TCMS_PRODUCT"] = app.config.get("KIWI_PRODUCT_NAME")
        os.environ["TCMS_PRODUCT_VERSION"] = app.config.get("KIWI_PRODUCT_VERSION")
        os.environ["TCMS_BUILD"] = str(uuid.uuid4())

    from trafficlight.http import adapter, root, status

    app.register_blueprint(adapter.bp)
    app.register_blueprint(status.bp)
    app.register_blueprint(root.bp)

    app.config["homerunner"] = HomerunnerClient(
        app.config["HOMERUNNER_URL"], app.config["SERVER_OVERRIDES"]
    )
    app.jinja_env.filters["delaytime"] = format_delaytime

    @app.before_serving
    async def startup() -> None:
        app.add_background_task(loop_cleanup_unresponsive_adapters)
        app.add_background_task(loop_check_for_new_tests)
        app.add_background_task(loop_check_all_tests_done)
        if kiwi.kiwi_client:
            await kiwi.kiwi_client.start_run()

    @app.after_serving
    async def shutdown() -> None:
        adapter.stop_background_tasks = True
        await adapter.interrupt_tasks()
        if kiwi.kiwi_client:
            await kiwi.kiwi_client.end_run()
        await adapter_shutdown()

        print("Results:\n")
        exit_code = 0
        total_tests = 0
        successful_tests = 0
        for testsuite in get_testsuites():
            print(
                f"\n{testsuite.name()}: {testsuite.successes()}/{len(testsuite.test_cases)} successful"
            )
            for testcase in testsuite.test_cases:
                print(f"  {testcase.client_types}: {testcase.state}")
                total_tests += 1
                if testcase.state != "success":
                    exit_code = 1
                else:
                    successful_tests = successful_tests + 1
                if testcase.state != "success" and testcase.state != "waiting":
                    for exception in testcase.exceptions:
                        print(exception)

        print(f"\nOverall: {successful_tests}/{total_tests} succeeded")
        os._exit(exit_code)

    return app
