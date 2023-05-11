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
            return {
                "action": "logout",
                "data": {
                 }
            }
        case 3: 
            return {
                "action": "login",
                "data": {
                    "localpart": "testuser_"+uuid,
                    "password": uuid
                 }
            }
        case 4: 
            return {
                "action": "exit",
                "data": { }
            }
    
    return {
        "action": "idle",
        "data": { }
    }
     
run()
