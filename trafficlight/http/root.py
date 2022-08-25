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

from quart import Blueprint, redirect, url_for

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

bp = Blueprint("root", __name__, url_prefix="/")


@bp.route("/", methods=["GET"])
async def redirect_status():  # type: ignore
    return redirect(url_for("status.index"))
