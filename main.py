import asyncio
import json
import logging
import time

import uvicorn
from fastapi import FastAPI, Request, Response
import aiohttp
from fastapi.responses import JSONResponse
from uvicorn.config import LOGGING_CONFIG

API_URL = "http://127.0.0.1:8889/"

app = FastAPI()
logger = logging.getLogger('uvicorn.error')
API_registry = {}


class API:
    def __init__(self, config: dict):
        self.identifier = config["identifier"]
        self.interval = config["rate_limit"]["interval"] * 1.01
        self.counter = 0
        self.rpd = config["rate_limit"].get("RPD",-1)
        self.lock = asyncio.Lock()
        self.last_call = 0.


def identifier_as_key(data: dict):
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def load_configs():
    global API_registry
    with open('apis.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    API_registry = {identifier_as_key(x["identifier"]): API(x) for x in data['sources']}


load_configs()


@app.post("/")
async def hello(request: Request):
    data = await request.json()
    req = data['request']
    # print(req['json'])
    api = API_registry[identifier_as_key(data['identifier'])]
    time_sleep = api.interval
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})


    async with api.lock:
        logger.info(f"acquire at {time.time()} by request {req['json']['msg']}")
        # to_sleep = max(0., time_sleep - (time.time() - api.last_call))
        # await asyncio.sleep(to_sleep)
        # api.last_call = time.time()
        await asyncio.sleep(time_sleep)
        api.counter = api.counter + 1
        API_registry[identifier_as_key(data['identifier'])] = api
    logger.info(f"release at {time.time()} by request {req['json']['msg']}")
    try:
        logger.info(f"session open at {time.time()} by request {req['json']['msg']}")
        async with aiohttp.ClientSession() as session:
            logger.info(f"making request at {time.time()} by request {req['json']['msg']}")
            async with session.request(**req) as resp:
                logger.info(f"got response at {time.time()} by request {req['json']['msg']}")
                r = JSONResponse(status_code=resp.status, content=await resp.json(), headers=resp.headers)
                logger.info(f"got response 100% at {time.time()} by request {req['json']['msg']}")
    except Exception as e:
        r = JSONResponse(content={"error": f"{type(e)} {str(e)}"})

    return r

#
# @app.post("/admin/api")
# async def add_api(cfg: dict):
#     name = cfg["name"]
#     api = APIConfig(name, cfg["url"], cfg["rate_limit"])
#     configs[name] = api
#     logger.info("new_api_registered", api=name)
#     return {"success": True}


if __name__ == "__main__":
    # Source - https://stackoverflow.com/questions/62934384/how-to-add-timestamp-to-each-request-in-uvicorn-logs
    # Posted by Yagiz Degirmenci
    # Retrieved 2025-11-05, License - CC BY-SA 4.0

    uvicorn.run(app, host="0.0.0.0", port=8000)
