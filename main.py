import asyncio
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config_loader import load_configs
from models.api_manager import APIManager

from logger import setup_logger

logger = setup_logger(__name__)
stop_event = None

class rateLimit(BaseModel):
    interval: float = 0.001
    RPD: int = -1
    add_random: bool = False


class APIModel(BaseModel):
    identifier: dict | str
    rate_limit: rateLimit


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
async def handle_request(request: Request):
    data = await request.json()
    req = data["request"]
    priority = data.get("priority", 1000000)
    api = APIManager.get(data["identifier"])
    if api is None:
        return JSONResponse(status_code=400, content={"msg": "Нет апи с таким идентификатором"})
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    api.counter += 1
    fut = asyncio.Future()
    await api.queue.put((priority, -time.time(), (fut, req)))
    return await fut


@app.post('/add_api')
async def add_api(cfg: APIModel):
    try:
        APIManager.add_api(cfg.model_dump())
        return JSONResponse(status_code=200, content={"data": "Api has been added"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": repr(e)})


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
