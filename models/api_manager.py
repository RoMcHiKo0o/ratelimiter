import asyncio
import json
import logging
from datetime import datetime, timedelta

from models.api import API

from logger import setup_logger

logger = setup_logger(__name__)

class APIManager:
    """Менеджер всех API-инстансов и фоновых задач."""
    _apis: dict[str, API] = {}
    _stop_event: asyncio.Event | None = None

    @classmethod
    def init(cls, configs: list[dict], stop_event: asyncio.Event):
        cls._stop_event = stop_event
        cls._apis = {
            cls._identifier_as_key(cfg["identifier"]): API(cfg, stop_event)
            for cfg in configs
        }
        logger.info(f"Инициализировано {len(cls._apis)} API")

    @classmethod
    def start(cls):
        if not cls._apis:
            raise RuntimeError("APIManager: нет инициализированных API")

        asyncio.create_task(cls._midnight_updater())
        for api in cls._apis.values():
            asyncio.create_task(api.worker())

    @classmethod
    async def _midnight_updater(cls):
        while not cls._stop_event.is_set():
            now = datetime.now()
            target = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())
            for api in cls._apis.values():
                api.counter = 0
            logger.info("✅ Обновил счётчики запросов в день")
            await asyncio.sleep(1)

    @classmethod
    def get(cls, identifier: dict) -> API:
        key = cls._identifier_as_key(identifier)
        return cls._apis[key]

    @staticmethod
    def _identifier_as_key(data: dict) -> str:
        return json.dumps(data, sort_keys=True, ensure_ascii=False)
