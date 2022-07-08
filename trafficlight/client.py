# vim: expandtab ts=4:
import functools
import logging
from trafficlight.model import Client, generate_model

logging.basicConfig(level=logging.DEBUG)
# Set transitions' log level to INFO; DEBUG messages will be omitted

#logging.getLogger('transitions').setLevel(logging.ERROR)
#logging.getLogger('wekzeug').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

bp = Blueprint("client", __name__, url_prefix="/client")


clients = []
models = []

@bp.route("/<string:uuid>/register", methods=["POST"])
def register(uuid):
    registration = request.json
    logger.info("%s (    ) registered: %s", uuid, registration)
    
    existing = get_client(uuid)
    if existing is not None:
        raise Error("Client already exists")
    
    client = Client(uuid, registration)
    clients.append(client)

    if len(clients) == 2:
       red = clients[0]
       green = clients[1]
       model = generate_model(red, green)
       models.append(model)
    return {}
   
def get_client(uuid):
    for client in clients:
       if client.uuid == uuid:
          return client
    return None

@bp.route("/<string:uuid>/poll", methods=["GET"])
def poll(uuid):
    client = get_client(uuid)
    if client is None:
        # Very bad situation; client belives it's registered; server has no record
        # do not update server state; tell client to exit and restart with new UUID.
        return {"action": "exit", "responses": []}

    return client.poll()



@bp.route("/<string:uuid>/respond", methods=["POST"])
def respond(uuid):
    client = get_client(uuid)
    if client is None:
        # Again, bad situation; client is doing something and no-one knows why
        raise Error("Unknown client performing update")
    update = request.json
    client.respond(update)

    return {}



