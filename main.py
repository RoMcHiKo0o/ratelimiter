"""
Главный модуль FastAPI приложения.
"""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config_loader import load_configs
from routers import admin_router, api_router
from logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    
    Инициализирует API менеджер при старте и корректно останавливает все задачи при завершении.
    """
    stop_event = asyncio.Event()
    
    # Загружаем конфигурации и создаём API менеджер
    api_manager = load_configs(stop_event)
    
    # Сохраняем в app.state для доступа из роутеров
    app.state.api_manager = api_manager
    app.state.stop_event = stop_event
    
    yield
    
    # Останавливаем все фоновые задачи
    logger.info("Setting stop event")
    stop_event.set()
    await asyncio.sleep(0)
    logger.info("DONE")


app = FastAPI(lifespan=lifespan)

# Подключаем роутеры
app.include_router(admin_router.router)
app.include_router(api_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
