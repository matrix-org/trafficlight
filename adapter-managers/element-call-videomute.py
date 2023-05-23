# Adapter tool to provide a very specific acceptance flow for an element call adapter.
from datetime import datetime

from quart import Quart, request

app = Quart(__name__)


def run() -> None:
    app.run()


uuid_response_count = {}


@app.post("/client/<uuid>/register")
async def register(uuid: str):
    print("registered")
    print(await request.get_data())
    uuid_response_count[uuid] = 0
    return {}


@app.post("/client/<uuid>/respond")
async def respond(uuid: str):
    print("responded:")
    print(await request.get_data())
    uuid_response_count[uuid] = uuid_response_count[uuid] + 1
    return {}


@app.post("/client/<uuid>/upload")
async def upload(uuid: str):
    print("Got upload")
    return {}


@app.get("/client/<uuid>/poll")
async def poll(uuid: str):
    count = uuid_response_count[uuid]
    print("polling")
    match count:
        case 0:
            return {
                "action": "register",
                "data": {"localpart": "testuser_" + uuid, "password": uuid},
            }
        case 1:
            return {
                "action": "set_display_name",
                "data": {
                    "display_name": "TestUser",
                },
            }
        case 2:
            return {
                "action": "create_or_join",
                "data": {
                    "call_name": "tl_test_two",
                },
            }
        case 3:
            return {"action": "lobby_join", "data": {}}
        case 4:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
        case 5:
            return {"action": "set_mute", "data": {"video_mute": True}}
        case 6:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
        case 7:
            return {"action": "set_mute", "data": {"video_mute": True}}
        case 8:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
        case 9:
            return {"action": "set_mute", "data": {"video_mute": False}}
        case 10:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
        case 11:
            return {"action": "set_mute", "data": {"video_mute": False}}
        case 12:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
        case 13:
            return {"action": "set_mute", "data": {"video_mute": True}}
        case 14:
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {"action": "idle", "data": {}}
    return {"action": "idle", "data": {}}


run()
