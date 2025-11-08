import asyncio
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, Response
import aiohttp
from fastapi.responses import JSONResponse

API_registry = {}
stop_event = None
logger = logging.getLogger('uvicorn.error')


@asynccontextmanager
async def lifespan(app):
    global stop_event
    stop_event = asyncio.Event()
    load_configs()
    yield
    logger.info('setting stop event')
    stop_event.set()
    await asyncio.sleep(0)
    logger.info('DONE')


app = FastAPI(lifespan=lifespan)


class API:
    def __init__(self, config: dict):
        self.identifier = config["identifier"]
        self.interval = config["rate_limit"]["interval"] * 1.01
        self.counter = 0
        self.rpd = config["rate_limit"].get("RPD", -1)
        self.queue = asyncio.Queue()

    async def worker(self):
        logger.info(F'worker is created')
        tasks = {}
        while not stop_event.is_set():
            # logger.info(F'worker is working')
            for fut,task in list(tasks.items()):
                if task.done():
                    tasks.pop(fut)
                    fut.set_result(await task)
                    self.queue.task_done()
            if not self.queue.empty():
                fut, req = await self.queue.get()
                logger.info(F'worker found task {req}')
                fut: asyncio.Future
                await asyncio.sleep(self.interval)
                logger.info(F'worker have slept for {req}')
                task = asyncio.create_task(make_request(req))
                logger.info(F'worker have created task {req}')
                tasks[fut] = task
                logger.info(F'worker got result for {req}')

            else:
                # logger.info(F'worker waits')
                # for x in asyncio.all_tasks():
                #     logger.info(x.get_coro())
                # for k,v in tasks:
                #     k.set_result(await v)
                #     self.queue.task_done()
                await asyncio.sleep(0)
        logger.info(f"{self.identifier} вышел с лупа")
        # logger.info(asyncio.all_tasks())


def identifier_as_key(data: dict):
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def load_configs() -> list[asyncio.Task]:
    # Создаем новый event loop для текущего потока
    global API_registry

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    with open('apis.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    logger.info(data)
    API_registry = {identifier_as_key(x["identifier"]): API(x) for x in data['sources']}

    return [asyncio.create_task(api.worker()) for api in API_registry.values()]


async def make_request(req):
    # logger.info(f"{datetime.fromtimestamp(time.time())} session open by request {req['json']['msg']}")
    # logger.info(f"{datetime.fromtimestamp(time.time())} making request by request {req['json']['msg']}")
    # for t in asyncio.all_tasks():
    #     logger.info(t.get_coro())
    # await asyncio.sleep(5)
    # logger.info(f"{datetime.fromtimestamp(time.time())} got response by request {req['json']['msg']}")
    # r = JSONResponse(status_code=200, content=req['json'])
    # logger.info(f"{datetime.fromtimestamp(time.time())} got response 100% by request {req['json']['msg']}")
    # return r
    logger.info(f'request {req}')
    for x in asyncio.all_tasks():
        logger.info(x.get_coro())
    try:
        logger.info(f"{datetime.fromtimestamp(time.time())} session open by request {req['json']['msg']}")
        async with aiohttp.ClientSession() as session:
            logger.info(f"{datetime.fromtimestamp(time.time())} making request by request {req['json']['msg']}")
            async with session.request(**req) as resp:
                logger.info(f"{datetime.fromtimestamp(time.time())} got response by request {req['json']['msg']}")
                task = asyncio.create_task(resp.json())
                r = JSONResponse(status_code=resp.status, content=await task, headers=resp.headers)
                logger.info(f"{datetime.fromtimestamp(time.time())} got response 100% by request {req['json']['msg']}")
    except Exception as e:
        r = JSONResponse(content={"error": f"{type(e)} {str(e)}"})
    return r


@app.post("/")
async def hello(request: Request):
    start = time.time()
    data = await request.json()
    req = data['request']
    logger.info(data)
    logger.info(API_registry)
    api: API = API_registry[identifier_as_key(data['identifier'])]
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    api.counter = api.counter + 1
    fut = asyncio.Future()
    await api.queue.put((fut,req))
    res = await fut
    logger.info(f'SENDING RESPONSE: {time.time()-start}')
    return res


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
