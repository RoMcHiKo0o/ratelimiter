import asyncio
import json
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
        for cfg in configs:
            key = cls._identifier_as_key(cfg)
            if key is not None:
                cls._apis[key] = API(cfg, stop_event)
        logger.info(f"Инициализировано {len(cls._apis)} API")

    @classmethod
    def start(cls):
        if not cls._apis:
            logger.warning("APIManager: нет инициализированных API")
            return

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
        return cls._apis.get(key, None)

    @staticmethod
    def _identifier_as_key(data: dict) -> str | None:
        if data is None:
            logger.info("Identifier can't be None")
            return None
        try:
            return json.dumps(data, sort_keys=True, ensure_ascii=False)
        except TypeError as e:
            logger.error(repr(e))
            logger.info(f"Can't serialize identifier {data}.")

    @classmethod
    def add_api(cls, cfg):
        ide = cls._identifier_as_key(cfg["identifier"])
        if ide is None:
            raise Exception("Identifier can't be None")
        if ide in cls._apis:
            raise Exception('Api with this identifier exists')
        api = API(cfg, cls._stop_event)
        cls._apis |= {ide: api}
        asyncio.create_task(api.worker())
