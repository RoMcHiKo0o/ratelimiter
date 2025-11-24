"""
Роутер для обработки API запросов.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from logger import setup_logger
from schemas import RequestIdentifierModel, HTTP_METHODS_LIST

logger = setup_logger(__name__)

router = APIRouter(tags=['Rate Limiter'])


@dataclass(order=True)
class Item:
    """Элемент очереди запросов с приоритетом."""
    priority: int
    item: Any = field(compare=False)


@router.api_route("/{url:path}", methods=HTTP_METHODS_LIST)
async def handle_request(request: Request, url: str):
    """
    Обрабатывает входящие HTTP запросы и направляет их в соответствующий API worker.
    
    Определяет идентификатор API по URL, методу и extra параметру,
    проверяет лимиты, добавляет запрос в очередь обработки.
    
    Args:
        request: FastAPI Request объект
        url: URL запроса
        
    Returns:
        JSONResponse с результатом выполнения запроса
    """
    # Получаем api_manager из app state
    api_manager = request.app.state.api_manager
    
    headers = dict(request.headers)
    ide_extra = headers.pop('x-identifier-extra', "")
    identifier_matcher = api_manager.get_identifier_matcher()
    ide = identifier_matcher.find_identifier(url, request.method, ide_extra, first_match_only=True)
    
    # Парсим JSON тело запроса (если есть)
    json_data = {}
    try:
        json_data = await request.json()
    except:
        pass
    
    # Формируем данные запроса
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
    
    # Обрабатываем приоритет из заголовка
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

