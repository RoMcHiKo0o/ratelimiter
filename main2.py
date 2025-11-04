import asyncio
import json
import time

import uvicorn
from fastapi import FastAPI, Request, Response
import aiohttp
from fastapi.responses import JSONResponse

API_URL = "http://127.0.0.1:8888/"

app = FastAPI()

API_registry = {}


class API:
    def __init__(self, config: dict):
        self.identifier = config["identifier"]
        self.interval = config["rate_limit"]["interval"] * 2
        self.counter = 0
        self.rpd = config["rate_limit"].get("RPD",-1)
        self.lock = asyncio.Lock()


def identifier_as_key(data: dict):
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def load_configs():
    global API_registry
    with open('apis.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    API_registry = {identifier_as_key(x["identifier"]): API(x) for x in data['sources']}


load_configs()

async def make_request(response: Response, req):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(**req) as resp:
                response.status_code = resp.status
                response.body = await resp.json()
                response.headers = resp.headers | {}
    except Exception as e:
        response.status_code = 404
        response.body = {"error": f"{type(e)} {str(e)}"}
    return response

@app.post("/")
async def hello(response:Response, request: Request):
    print(time.time())
    data = await request.json()
    req = data['request']
    print(req['json'])
    api = API_registry[identifier_as_key(data['identifier'])]
    time_sleep = api.interval
    async with api.lock:
        await asyncio.sleep(time_sleep)
        if api.counter == api.rpd:
            response.status_code = 429
            response.body = {"msg": "Достигнут лимит запросов в сутки"}
        api.counter = api.counter + 1
        API_registry[identifier_as_key(data['identifier'])] = api
    return await make_request(response,req)


#
# @app.post("/admin/api")
# async def add_api(cfg: dict):
#     name = cfg["name"]
#     api = APIConfig(name, cfg["url"], cfg["rate_limit"])
#     configs[name] = api
#     logger.info("new_api_registered", api=name)
#     return {"success": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
