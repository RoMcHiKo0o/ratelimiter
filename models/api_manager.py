import asyncio
from datetime import datetime, timedelta

from models.api import API

from logger import setup_logger
from schemas import IdentifierModel

logger = setup_logger(__name__)


class APIManager:
    """Менеджер всех API-инстансов и фоновых задач."""
    _apis: dict[str, API] = {}
    _stop_event: asyncio.Event | None = None

    @classmethod
    def init(cls, configs: list[dict], stop_event: asyncio.Event):
        cls._stop_event = stop_event
        for cfg in configs:
            v = cfg.get("identifier", None)
            try:
                cfg["identifier"] = str(IdentifierModel(value=v))
                cls._apis[cfg["identifier"]] = API(cfg, stop_event)
            except ValueError as e:
                logger.error(repr(e))
            except Exception as e:
                logger.error(f"Unexpected error:  {repr(e)}")

        logger.info(f"Инициализировано {len(cls._apis)} API")

    @classmethod
    def start(cls):
        if not cls._apis:
            logger.info("APIManager: нет инициализированных API")
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
    def get(cls, key: str) -> API | None:
        return cls._apis.get(key, None)

    @classmethod
    def add_api(cls, cfg):
        ide = cfg["identifier"]
        if ide in cls._apis:
            raise Exception('Api with this identifier exists')
        api = API(cfg, cls._stop_event)
        cls._apis |= {ide: api}
        asyncio.create_task(api.worker())

    @classmethod
    def get_all_apis(cls):
        return cls._apis
