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
import io
import logging
from typing import List

from flask import Blueprint, abort, render_template, request, send_file, typing

from trafficlight.store import get_clients, get_test, get_tests

logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted

# logging.getLogger('transitions').setLevel(logging.ERROR)
# logging.getLogger('wekzeug').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=["GET"])
def index() -> typing.ResponseValue:
    return render_template(
        "status_index.j2.html", clients=get_clients(), tests=get_tests()
    )


class TestCase(object):
    def __init__(self, name, state, time):
        self.failure = True if state == "failure" else False
        self.error = True if state == "error" else False
        self.skipped = True if state == "skipped" else False
        self.time = time
        self.name = name


class TestSuite(object):
    def __init__(self, name, testcases: List[TestCase]):
        self.name = name
        self.failures = 0 + sum(1 for tc in testcases if tc.failure)
        self.errors = 0 + sum(1 for tc in testcases if tc.error)
        self.skipped = 0 + sum(1 for tc in testcases if tc.skipped)
        self.tests = len(testcases)
        self.testcases = testcases


@bp.route("/junit.xml", methods=["GET"])
def as_junit() -> typing.ResponseValue:

    # for now we assume there's only one test; when we add the second we'll need to expand this logic a bit.
    tests = get_tests()
    testcases = []
    for test in tests:
        if test.model is not None:
            if test.model.state == "complete":
                testcases.append(TestCase(test.description, "success", 0))
            elif test.model.state == "failure":
                testcases.append(TestCase(test.description, "failure", 0))
            else:
                # tests that haven't completed are currently going to be 'failed' in my book.
                # perhaps map to error ? idk.
                testcases.append(TestCase(test.description, "error", 0))
        else:
            testcases.append(TestCase(test.description, "skipped", 0))

    testsuite = TestSuite("check verification", testcases)
    testsuites = [testsuite]

    return render_template(
        "junit.j2.xml",
        testsuites=testsuites,
        errors=testsuite.errors,
        failures=testsuite.failures,
        skipped=testsuite.skipped,
        tests=testsuite.tests,
    )


@bp.route("/<string:uuid>/context.png", methods=["GET"])
def test_context_image(uuid: str) -> typing.ResponseValue:
    test = get_test(uuid)
    if test is not None and test.model is not None:
        b = io.BytesIO()
        test.model.render_local_region(b)
        b.seek(0)
        return send_file(b, mimetype="image/png")
    else:
        abort(404)


@bp.route("/<string:uuid>/statemachine.png", methods=["GET"])
def test_image(uuid: str) -> typing.ResponseValue:
    test = get_test(uuid)
    if test is not None and test.model is not None:
        b = io.BytesIO()
        test.model.render_whole_graph(b)
        b.seek(0)
        return send_file(b, mimetype="image/png")
    else:
        abort(404)


@bp.route("/<string:uuid>/status", methods=["GET"])
def test_status(uuid: str) -> typing.ResponseValue:
    refresh = request.args.get("refresh", default=0, type=int)
    logger.info("Finding test %s", uuid)
    test = get_test(uuid)
    if test is not None:
        return render_template("status_model.j2.html", test=test, refresh=refresh)
    else:
        abort(404)
