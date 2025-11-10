import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config_loader import load_configs
from models.api_manager import APIManager

from logger import setup_logger

logger = setup_logger(__name__)
stop_event = None

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

    api = APIManager.get(data["identifier"])
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})

    api.counter += 1
    fut = asyncio.Future()
    await api.queue.put((fut, req))
    return await fut


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)