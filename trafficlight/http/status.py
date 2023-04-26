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
from typing import List

from quart import Blueprint, abort, render_template, request, send_file

from trafficlight.internals.testsuite import TestSuite
from trafficlight.store import (
    get_adapters,
    get_test_case,
    get_tests,
    get_testsuite,
    get_testsuites,
)

logger = logging.getLogger(__name__)

bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=["GET"])
async def index():  # type: ignore
    return await render_template(
        "status_index.j2.html",
        completed_adapters=get_adapters(True),
        inprogress_adapters=get_adapters(False),
        tests=get_tests(),
        test_suites=get_testsuites(),
    )


@bp.route("/junit.xml", methods=["GET"])
async def as_junit():  # type: ignore
    # for now we assume there's only one test; when we add the second we'll need to expand this logic a bit.
    testsuites: List[TestSuite] = get_testsuites()

    errors = 0 + sum(suite.errors() for suite in testsuites)
    failures = 0 + sum(suite.failures() for suite in testsuites)
    skipped = 0 + sum(suite.waiting() for suite in testsuites)
    test_count = 0 + sum(len(suite.test_cases or []) for suite in testsuites)

    return await render_template(
        "junit.j2.xml",
        testsuites=testsuites,
        errors=errors,
        failures=failures,
        skipped=skipped,
        tests=test_count,
    )


@bp.route("/<string:guid>/files/<string:name>", methods=["GET"])
async def test_file(guid: str, name: str):  # type: ignore
    test = get_test_case(guid)
    logger.info("Getting ${guid} ${name}")
    if name in test.files:
        path = test.files[name]
        return await send_file(path)
    else:
        abort(404)


@bp.route("/<string:guid>/suitestatus", methods=["GET"])
async def testsuite_status(guid: str):  # type: ignore
    refresh = request.args.get("refresh", default=0, type=int)  # type: ignore
    testsuite = get_testsuite(guid)
    if testsuite is not None:
        return await render_template(
            "status_suite.j2.html", testsuite=testsuite, refresh=refresh
        )
    else:
        abort(404)


@bp.route("/<string:guid>/status", methods=["GET"])
async def testcase_status(guid: str):  # type: ignore
    refresh = request.args.get("refresh", default=0, type=int)  # type: ignore
    logger.info("Finding test %s", guid)
    test = get_test_case(guid)
    if test is not None:
        return await render_template("status_case.j2.html", test=test, refresh=refresh)
    else:
        abort(404)
