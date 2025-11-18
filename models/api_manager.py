import asyncio
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

from models.api import API

from logger import setup_logger
from schemas import APIModel

logger = setup_logger(__name__)


def get_sub_urls(url: str):
    parsed_url = urlparse(url)
    l = urlparse(url).path.split('/')
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return [urljoin(base_url, '/'.join(l[:i + 1])) for i in range(len(l))]


def get_identifier(url: str, method: str, extra: str, first: bool = True) -> dict[str, str] | None:
    res = []
    for key in APIManager.get_all_apis().keys():
        ide = json.loads(key)
        if ide.get("extra", "") != extra:
            continue
        ide_method = ide.get("method")
        if not (method == ide_method or ide_method == "ANY" or (method == "ANY" and not first)):
            continue
        for sub_url in get_sub_urls(url)[::-1]:
            if sub_url == ide.get("url"):
                v = {"url": sub_url, "method": ide_method, "extra": extra}
                if first:
                    return v
                res.append(v)
    return None if first else res


def is_ide_conflicted(ide_str: str):
    ide = json.loads(ide_str)
    same_ides = get_identifier(ide["url"], ide["method"], ide["extra"], first=False)
    if len(same_ides):
        logger.error(f"Identifier: {ide}. Overlapping identifiers: {same_ides}")
        return same_ides
    return False


class APIManager:
    """Менеджер всех API-инстансов и фоновых задач."""
    _apis: dict[str, API] = {}
    _stop_event: asyncio.Event | None = None

    @classmethod
    def init(cls, configs: list[dict], stop_event: asyncio.Event):
        cls._stop_event = stop_event
        for cfg in configs:
            try:
                cfg_model = APIModel(**cfg)
                if not is_ide_conflicted(cfg_model.identifier):
                    cls._apis[cfg_model.identifier] = API(cfg_model, stop_event)
            except (ValueError, KeyError, TypeError) as e:
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
    def add_api(cls, cfg: APIModel):
        ide = cfg.identifier
        if ide in cls._apis:
            raise Exception(f'Api with this identifier exists: {ide}')
        api = API(cfg, cls._stop_event)
        cls._apis |= {ide: api}
        asyncio.create_task(api.worker())

    @classmethod
    def get_all_apis(cls):
        return cls._apis
