# vim: expandtab ts=4:
import functools
import logging
import io
from trafficlight.store import get_clients, get_tests, get_test

logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted

#logging.getLogger('transitions').setLevel(logging.ERROR)
#logging.getLogger('wekzeug').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_file,
)

bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=["GET"])
def index():
    return render_template("status_index.j2.html", clients = get_clients(), tests=get_tests())
   

@bp.route("/<string:uuid>/context.png", methods=["GET"])
def test_context_image(uuid):
    test = get_test(uuid)
    if test is not None:
       b = io.BytesIO()
       test.model.render_local_region(b)
       b.seek(0)
       return send_file(b, mimetype="image/png")
    else:
       abort(404)

@bp.route("/<string:uuid>/statemachine.png", methods=["GET"])
def test_image(uuid):
    test = get_test(uuid)
    if test is not None:
       b = io.BytesIO()
       test.model.render_whole_graph(b)
       b.seek(0)
       return send_file(b, mimetype="image/png")
    else:
       abort(404)

@bp.route("/<string:uuid>/status", methods=["GET"])
def test_status(uuid):
    logger.info("Finding test %s", uuid)
    test = get_test(uuid)
    if test is not None:
       return render_template("status_model.j2.html", test = test) 
    else:
       abort(404)
