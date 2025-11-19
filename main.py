import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config_loader import load_configs
from models.api_manager import api_manager, get_identifier, is_ide_conflicted

from logger import setup_logger
from schemas import RequestIdentifierModel, HTTP_METHODS_LIST, APIModel

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


@app.post('/add_api')
async def add_api(cfg: APIModel):
    res = is_ide_conflicted(cfg.identifier)
    if res:
        return JSONResponse(status_code=400, content={"error": f"Identifiers with overlapping areas of influence were found."})
    try:
        api_manager.add_api(cfg)
        return JSONResponse(status_code=200, content={"data": "Api has been added"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": repr(e)})


@app.get('/get_apis')
async def get_apis():
    return JSONResponse(status_code=200, content=list(api_manager.get_all_apis().keys()))


@app.api_route("/{url:path}", methods=HTTP_METHODS_LIST)
async def handle_request(request: Request, url: str):
    headers = dict(request.headers)
    ide_extra = headers.pop('x-identifier-extra', "")
    ide = get_identifier(url, request.method, ide_extra)
    json_data = {}
    try:
        json_data = await request.json()
    except:
        pass
    req_data = {
        "identifier": ide,
        "request": {
            "url": url,
            "method": request.method,
            "headers": headers,
            "params": request.query_params,
            "json": json_data
        }
    }
    priority = headers.pop('x-priority', 0)

    try:
        priority = int(priority)
        req_data['priority'] = priority
    except:
        logger.warning(f'Priority have to be int-like string, got {priority=}')

    req = RequestIdentifierModel(**req_data)
    api = api_manager.get(req.identifier)
    if api is None:
        return JSONResponse(status_code=400, content={"msg": "Нет апи с таким идентификатором"})
    if api.counter == api.rpd:
        return JSONResponse(status_code=429, content={"msg": "Достигнут лимит запросов в сутки"})
    api.counter += 1
    fut = asyncio.Future()
    item = Item(-priority, (fut, req.request.model_dump()))
    await api.queue.put(item)
    return await fut


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
