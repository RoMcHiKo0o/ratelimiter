import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, Request
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


async def midnight_updater():
    while not stop_event.is_set():
        now = datetime.now()
        tomorrow = (now).replace(hour=17, minute=5, second=0, microsecond=0)
        wait_seconds = (tomorrow - now).total_seconds()

        await asyncio.sleep(wait_seconds)
        for api in API_registry.values():
            api.counter = 0
        logger.info("Обновил счётчики запросов в день")
        await asyncio.sleep(1)


class API:
    def __init__(self, config: dict):
        self.identifier = config["identifier"]
        self.interval = config.get("rate_limit", {}).get("interval", 0.001) * 1.01
        self.counter = 0
        self.rpd = config.get("rate_limit", {}).get("RPD", -1)
        self.queue = asyncio.Queue()

    async def worker(self):
        logger.info(F'worker is created')
        tasks = {}
        while not stop_event.is_set():

            for fut, task in list(tasks.items()):
                if task.done():
                    tasks.pop(fut)
                    fut.set_result(await task)
                    self.queue.task_done()
            if not self.queue.empty():
                fut, req = await self.queue.get()
                logger.info(F'worker found task {req}')
                task = asyncio.create_task(make_request(req))
                logger.info(F'worker have created task {req}')
                tasks[fut] = task
                logger.info(F'worker have slept for {req}')
                await asyncio.sleep(self.interval)

            else:
                await asyncio.sleep(0)
        logger.info(f"{self.identifier} вышел с event loop")


def identifier_as_key(data: dict):
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def load_configs() -> list[asyncio.Task]:
    global API_registry

    with open('apis.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    logger.info(data)
    API_registry = {identifier_as_key(x["identifier"]): API(x) for x in data['sources']}
    asyncio.create_task(midnight_updater())
    return [asyncio.create_task(api.worker()) for api in API_registry.values()]


async def make_request(req):
    logger.info(f'request {req}')
    try:
        logger.info(f"{datetime.fromtimestamp(time.time())} session open by request {req['json']['msg']}")
        async with aiohttp.ClientSession() as session:
            logger.info(f"{datetime.fromtimestamp(time.time())} making request by request {req['json']['msg']}")
            async with session.request(**req) as resp:
                logger.info(f"{datetime.fromtimestamp(time.time())} got response by request {req['json']['msg']}")
                r = JSONResponse(status_code=resp.status, content=await resp.json(), headers=resp.headers)
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
    await api.queue.put((fut, req))
    res = await fut
    logger.info(f'SENDING RESPONSE: {time.time() - start}')
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
