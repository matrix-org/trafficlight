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
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from quart import Quart

import trafficlight
from trafficlight.http.adapter import (
    adapter_shutdown,
    loop_check_for_new_tests,
    loop_cleanup_unresponsive_adapters,
)
from trafficlight.internals.testsuite import TestSuite
from trafficlight.store import add_testsuite
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
        }
    )

    # Allows override via env var: TRAFFICLIGHT_<key>;
    app.config.from_prefixed_env(prefix="TRAFFICLIGHT")

    # TODO: ensure uploads folder is available
    # can i create README.md in there with a comment, for instance...

    # ensure the instance folder exists
    print(f"{app.config}")

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

    from trafficlight.http import adapter, root, status

    app.register_blueprint(adapter.bp)
    app.register_blueprint(status.bp)
    app.register_blueprint(root.bp)

    app.jinja_env.filters["delaytime"] = format_delaytime

    @app.before_serving
    async def startup() -> None:
        app.add_background_task(loop_cleanup_unresponsive_adapters)
        app.add_background_task(loop_check_for_new_tests)

    @app.after_serving
    async def shutdown() -> None:
        trafficlight.http.adapter.stop_background_tasks = True
        await adapter_shutdown()

    return app
