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

from quart import Blueprint, abort, current_app, render_template, request, send_file

from trafficlight.store import (
    get_clients,
    get_test,
    get_tests,
    get_testsuite,
    get_testsuites,
)
from trafficlight.tests import TestSuite

logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted

# logging.getLogger('transitions').setLevel(logging.ERROR)
# logging.getLogger('wekzeug').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=["GET"])
async def index():  # type: ignore
    return await render_template(
        "status_index.j2.html",
        clients=get_clients(),
        tests=get_tests(),
        test_suites=get_testsuites(),
    )


@bp.route("/junit.xml", methods=["GET"])
async def as_junit():  # type: ignore
    # for now we assume there's only one test; when we add the second we'll need to expand this logic a bit.
    testsuites: List[TestSuite] = get_testsuites()

    errors = 0 + sum(suite.errors() for suite in testsuites)
    failures = 0 + sum(suite.failures() for suite in testsuites)
    skipped = 0 + sum(suite.skipped() for suite in testsuites)
    test_count = 0 + sum(len(suite.test_cases or []) for suite in testsuites)

    return await render_template(
        "junit.j2.xml",
        testsuites=testsuites,
        errors=errors,
        failures=failures,
        skipped=skipped,
        tests=test_count,
    )


@bp.route("/<string:uuid>/context.png", methods=["GET"])
async def test_context_image(uuid: str):  # type: ignore
    test = get_test(uuid)
    if test is not None and test.model is not None:
        b = io.BytesIO()
        test.model.render_local_region(b)
        b.seek(0)
        return await send_file(b, mimetype="image/png")
    else:
        return await send_file("trafficlight/static/no_model.png", mimetype="image/png")


@bp.route("/<string:uuid>/statemachine.png", methods=["GET"])
async def test_image(uuid: str):  # type: ignore
    test = get_test(uuid)
    if test is not None and test.model is not None:
        b = io.BytesIO()
        test.model.render_whole_graph(b)
        b.seek(0)
        return await send_file(b, mimetype="image/png")
    else:
        return await send_file("trafficlight/static/no_model.png", mimetype="image/png")


@bp.route("/<string:uuid>/files/<string:name>", methods=["GET"])
async def test_file(uuid: str, name: str):  # type: ignore
    test = get_test(uuid)
    logger.info("Getting ${uuid} ${name}")
    if name in test.model.files:
        path = test.model.files[name]
        return await send_file(path)
    else:
        abort(404)


@bp.route("/<string:uuid>/suitestatus", methods=["GET"])
async def testsuite_status(uuid: str):  # type: ignore
    refresh = request.args.get("refresh", default=0, type=int)
    testsuite = get_testsuite(uuid)
    if testsuite is not None:
        return await render_template(
            "status_suite.j2.html", testsuite=testsuite, refresh=refresh
        )
    else:
        abort(404)


@bp.route("/<string:uuid>/status", methods=["GET"])
async def testcase_status(uuid: str):  # type: ignore
    refresh = request.args.get("refresh", default=0, type=int)
    logger.info("Finding test %s", uuid)
    test = get_test(uuid)
    if test is not None:
        return await render_template("status_case.j2.html", test=test, refresh=refresh)
    else:
        abort(404)
