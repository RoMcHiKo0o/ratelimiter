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

API_URL = "http://127.0.0.1:8889/"
API_registry = {}
stop_event = None


@asynccontextmanager
async def lifespan(app):
    global stop_event
    stop_event = threading.Event()
    print(asyncio.all_tasks())
    thread = threading.Thread(target=load_configs)
    thread.start()
    print(asyncio.all_tasks())
    yield
    logger.info('setting stop event')
    stop_event.set()
    logger.info('joining thread')
    print(asyncio.all_tasks())
    thread.join(5.5)
    logger.info('joining thread finished')
    print(asyncio.all_tasks())
    logger.info('DONE')


logger = logging.getLogger('uvicorn.error')

app = FastAPI(lifespan=lifespan)


class API:
    def __init__(self, config: dict):
        self.identifier = config["identifier"]
        self.interval = config["rate_limit"]["interval"] * 1.01
        self.counter = 0
        self.rpd = config["rate_limit"].get("RPD", -1)
        self.queue = asyncio.Queue()

    async def worker(self):
        while not stop_event.is_set():
            print(self.identifier)
            if not self.queue.empty():
                fut, req = await self.queue.get()
                fut: asyncio.Future
                await asyncio.sleep(self.interval)
                self.counter = self.counter + 1
                result = await make_request(req)
                fut.set_result(result)
                self.queue.task_done()
            else:
                await asyncio.sleep(1)
        logger.info(f"{self.identifier} вышел с лупа")
        print(asyncio.all_tasks())


def identifier_as_key(data: dict):
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def load_configs():
    # Создаем новый event loop для текущего потока
    global API_registry

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with open('apis.json', 'r', encoding='utf8') as f:
        data = json.load(f)
    print(data)
    API_registry = {identifier_as_key(x["identifier"]): API(x) for x in data['sources']}

    # Привязываем loop к текущему потоку

    # Добавляем задачи в новый event loop
    for api in API_registry.values():
        loop.create_task(api.worker())

    # Запускаем все задачи в event loop
    loop.run_forever()


async def make_request(req):
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
    data = await request.json()
    req = data['request']
    print(data)
    print(API_registry)
    api: API = API_registry[identifier_as_key(data['identifier'])]
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    fut = asyncio.Future()
    await api.queue.put((fut, req))
    return await fut


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
