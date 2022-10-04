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

from trafficlight.store import add_testsuite
from trafficlight.tests import load_test_suites

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

logging.getLogger("transitions").setLevel(logging.ERROR)


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
            "TEST_PATTERN": "/**/invited_user_decrypt_prejoin_messages_more_clients_testsuite.py",
            "SERVER_TYPES": "Synapse",
            "CLIENT_TYPES": "ElementWeb",
            "UPLOAD_FOLDER": "/tmp/",
        }
    )

    # Allows override via env var: TRAFFICLIGHT_<key>;
    app.config.from_prefixed_env(prefix="TRAFFICLIGHT")

    # TODO: ensure uploads folder is available
    # can i create README.md in there with a comment, for instance...

    app.config["SERVER_TYPES"] = app.config["SERVER_TYPES"].split(",")
    app.config["CLIENT_TYPES"] = app.config["CLIENT_TYPES"].split(",")

    # ensure the instance folder exists
    print(f"{app.config}")

    suites = load_test_suites(
        app.config.get("TEST_PATTERN"),
        app.config.get("SERVER_TYPES"),
        app.config.get("CLIENT_TYPES"),
    )
    for suite in suites:
        logger.info(f"Generating test cases for {suite.name()}")
        suite.generate_test_cases()
        add_testsuite(suite)

    from trafficlight.http import client, root, status

    app.register_blueprint(client.bp)
    app.register_blueprint(status.bp)
    app.register_blueprint(root.bp)

    app.jinja_env.filters["delaytime"] = format_delaytime

    return app
