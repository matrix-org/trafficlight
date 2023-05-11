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
                "data": {
                    "localpart": "testuser_"+uuid,
                    "password": uuid
                 }
            }
        case 1: 
            return {
                "action": "set_display_name",
                "data": {
                    "display_name": "TestUser",
                 }
            }
        case 2: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 3:
            return {
                "action": "create_or_join",
                "data": {
                    "call_name": "tl_test",
                 }
            }
        case 4: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 5: 
            return {
                "action": "get_lobby_data",
                "data": {
                 }
            }
        case 6: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 7:
            return {
                "action": "lobby_join",
                "data": {
                 }
            }
        case 8: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 9:
            return {
                "action": "get_call_data",
                "data": {
                 }
            }
        case 10: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 11:
            return {
                "action": "join_by_url",
                "data": {
                   "call_url": "http://localhost:4173/tl_test"
                }
            } 
        case 12: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 13:
            return {
                "action": "lobby_join",
                "data": {
                 }
            }
        case 14: 
            uuid_response_count[uuid] = uuid_response_count[uuid] + 1
            return {
                "action": "idle",
                "data": { }
            }
        case 15:
            return {
                "action": "get_call_data",
                "data": {
                 }
            }
    return {
        "action": "idle",
        "data": { }
    }
     
run()
