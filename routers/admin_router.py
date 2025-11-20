"""
Административный роутер для управления API.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from logger import setup_logger
from schemas import APIModel

logger = setup_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post('/add_api')
async def add_api(request: Request, cfg: APIModel):
    """
    Добавляет новый API в менеджер.
    
    Проверяет наличие конфликтов идентификаторов перед добавлением.
    
    Args:
        request: FastAPI Request объект
        cfg: Конфигурация API для добавления
        
    Returns:
        JSONResponse с результатом операции
    """
    api_manager = request.app.state.api_manager
    identifier_matcher = api_manager.get_identifier_matcher()
    
    if identifier_matcher.has_conflict(cfg.identifier):
        return JSONResponse(
            status_code=400, 
            content={"error": "Identifiers with overlapping areas of influence were found."}
        )
    
    try:
        api_manager.add_api(cfg)
        return JSONResponse(status_code=200, content={"data": "Api has been added"})
    except Exception as e:
        logger.error(f"Ошибка при добавлении API: {repr(e)}")
        return JSONResponse(status_code=400, content={"error": repr(e)})


@router.get('/get_apis')
async def get_apis(request: Request):
    """
    Возвращает список всех зарегистрированных API.
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        JSONResponse со списком идентификаторов API
    """
    api_manager = request.app.state.api_manager
    return JSONResponse(
        status_code=200, 
        content=list(api_manager.get_all_apis().keys())
    )

