import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config_loader import load_configs
from models.api_manager import APIManager

from logger import setup_logger
from schemas import RequestIdentifierModel, APIModel

logger = setup_logger(__name__)
stop_event = None


@dataclass(order=True)
class Item:
    priority: int
    item: Any = field(compare=False)


@asynccontextmanager
async def lifespan(app):
    global stop_event
    stop_event = asyncio.Event()

    load_configs(stop_event)
    yield

    logger.info("Setting stop event")
    stop_event.set()
    await asyncio.sleep(0)
    logger.info("DONE")


app = FastAPI(lifespan=lifespan)


@app.post("/")
async def handle_request(request: RequestIdentifierModel):
    req = request.request
    priority = request.priority
    api = APIManager.get(request.identifier.value)
    if api is None:
        return JSONResponse(status_code=400, content={"msg": "Нет апи с таким идентификатором"})
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    api.counter += 1
    fut = asyncio.Future()
    item = Item(-priority, (fut, req))
    await api.queue.put(item)
    return await fut


@app.post('/add_api')
async def add_api(cfg: APIModel):
    try:
        APIManager.add_api(cfg.model_dump())
        return JSONResponse(status_code=200, content={"data": "Api has been added"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": repr(e)})


@app.get('/get_apis')
async def get_apis():
    return JSONResponse(status_code=200, content=list(APIManager.get_all_apis().keys()))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
