# Adapter tool to provide a very specific acceptance flow for an element call adapter.
from datetime import datetime
from quart import Quart, request
app = Quart(__name__)

def run() -> None:
    app.run()

uuid_response_count = {}

@app.post("/client/<uuid>/upload")
async def upload(uuid:str):
    print("File uploaded...")
    return {}

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

@app.get("/client/<uuid>/poll")
async def poll(uuid: str):
    count = uuid_response_count[uuid]
    print("polling")
    match count:
        case 0: 
            return {
                "action": "create_or_join",
                "data": {
                    #"callName": "trafficlight_" + str(datetime.now().timestamp()),
                    "callName": "trafficlight_asdf",
                    "displayName": "user_"+str(datetime.now().timestamp())
                 }
            }
        case 1: 
            return {
                "action": "lobby_join",
                "data": { }
            }
        case 2: 
            return {
                "action": "start_screenshare",
                "data": { }
            }
        case 3: 
            return {
                "action": "idle",
                "data": { }
            }
    
    return {
        "action": "idle",
        "data": { }
    }
     
run()
