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
import os
import typing
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Flask

import trafficlight.tests
from trafficlight.store import Client, TestCase, add_test, generate_model


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


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import client, status

    app.register_blueprint(client.bp)
    app.register_blueprint(status.bp)
    app.jinja_env.filters["delaytime"] = format_delaytime

    def android_matcher(x: Client) -> bool:
        return str(x.registration["type"]) == "element-android"

    def web_matcher(x: Client) -> bool:
        return str(x.registration["type"]) == "element-web"

    clients = {
        "android,web": [android_matcher, web_matcher],
        "web,android": [web_matcher, android_matcher],
        "web,web": [web_matcher, web_matcher],
        "android, android": [android_matcher, android_matcher]
    }
    for suite_config in trafficlight.tests.tests:
        cases: typing.List[TestCase] = []
        for (key, value) in clients.items():
            case = TestCase(uuid.uuid4(),
                            key,
                            value,
                            suite_config.generate_model,
                            suite_config.validate_results)
            add_test(case)
            cases.append(case)
        suite = trafficlight.status.TestSuite(suite_config.__name__, cases)

    # Maybe even write them to a report afterwards
    return app
