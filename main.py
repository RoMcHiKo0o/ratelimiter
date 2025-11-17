import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Annotated

import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse

from config_loader import load_configs
from models.api_manager import APIManager

from logger import setup_logger
from schemas import RequestIdentifierModel, HTTP_METHODS_LIST, APIModel

logger = setup_logger(__name__)
stop_event = None


def get_identifier(url, method):
    ...


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


@app.post('/add_api')
async def add_api(cfg: APIModel):
    try:
        APIManager.add_api(cfg)
        return JSONResponse(status_code=200, content={"data": "Api has been added"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": repr(e)})


@app.get('/get_apis')
async def get_apis():
    return JSONResponse(status_code=200, content=list(APIManager.get_all_apis().keys()))


@app.api_route("/{url:path}", methods=HTTP_METHODS_LIST)
async def handle_request(request: Request, url: str, priority: Annotated[int, Query()] = 0):
    # ide = get_identifier(url, request.method)
    ide = (await request.json())['identifier']
    params = dict(request.query_params)
    params.pop("priority", None)
    req_data = {
        "identifier": ide,
        "request": {
            "url": url,
            "method": request.method,
            "headers": request.headers,
            "params": request.query_params,
            "json": await request.json()
        },
        "priority": priority
    }
    req = RequestIdentifierModel(**req_data)
    return req.model_dump()
    api = APIManager.get(req.identifier)
    if api is None:
        return JSONResponse(status_code=400, content={"msg": "Нет апи с таким идентификатором"})
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    api.counter += 1
    fut = asyncio.Future()
    item = Item(-priority, (fut, req))
    await api.queue.put(item)
    return await fut


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
