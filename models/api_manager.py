"""
Менеджер API-инстансов и фоновых задач.

Отвечает за:
- Инициализацию и управление жизненным циклом API-инстансов
- Запуск фоновых задач (workers, daily counter reset)
- Предоставление доступа к API по идентификаторам
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from models.api import API
from services.identifier_matcher import IdentifierMatcher

from logger import setup_logger
from schemas import APIModel

logger = setup_logger(__name__)


class APIManager:
    """
    Менеджер всех API-инстансов и фоновых задач.
    
    Управляет жизненным циклом API-инстансов, запускает workers для обработки запросов
    и выполняет периодические задачи (например, сброс счётчиков в полночь).
    """

    def __init__(self, configs: list[dict], stop_event: asyncio.Event):
        """
        Инициализация менеджера API.
        
        Args:
            configs: Список конфигураций API
            stop_event: Событие для остановки всех фоновых задач
        """
        self._apis: dict[str, API] = {}
        self._stop_event = stop_event
        self._identifier_matcher = IdentifierMatcher(self)
        
        self._initialize_apis(configs)
        logger.info(f"Инициализировано {len(self._apis)} API")

    def _initialize_apis(self, configs: list[dict]) -> None:
        """
        Инициализирует API из списка конфигураций.
        
        Пропускает конфигурации с ошибками валидации или конфликтующими идентификаторами.
        
        Args:
            configs: Список конфигураций API
        """
        for cfg in configs:
            try:
                cfg_model = APIModel(**cfg)
                
                if self._identifier_matcher.has_conflict(cfg_model.identifier):
                    continue
                
                self._apis[cfg_model.identifier] = API(cfg_model, self._stop_event)
                
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Ошибка валидации конфигурации API: {repr(e)}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при инициализации API: {repr(e)}")

    def start(self) -> None:
        """
        Запускает все фоновые задачи:
        - Задачи для сброса счётчиков в полночь
        - Workers для каждого API-инстанса
        """
        if not self._apis:
            logger.info("APIManager: нет инициализированных API")
            return

        asyncio.create_task(self._midnight_updater())
        for api in self._apis.values():
            asyncio.create_task(api.worker())

    async def _midnight_updater(self) -> None:
        """
        Фоновая задача, сбрасывающая счётчики запросов всех API в полночь.
        
        Работает в бесконечном цикле до установки stop_event.
        """
        if self._stop_event is None:
            logger.warning("APIManager: stop_event не установлен, обновление счётчиков отменено")
            return

        while not self._stop_event.is_set():
            now = datetime.now()
            # Вычисляем время следующей полночи
            target = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (target - now).total_seconds()
            
            await asyncio.sleep(sleep_seconds)
            
            # Сбрасываем счётчики всех API
            self._reset_all_counters()
            
            logger.info("✅ Обновил счётчики запросов в день")
            await asyncio.sleep(1)  # Небольшая задержка перед следующим циклом

    def _reset_all_counters(self) -> None:
        """Сбрасывает счётчики запросов для всех API-инстансов."""
        for api in self._apis.values():
            api.counter = 0

    def get(self, identifier_key: str) -> Optional[API]:
        """
        Получает API-инстанс по ключу идентификатора.
        
        Args:
            identifier_key: JSON-строка идентификатора
            
        Returns:
            API-инстанс или None, если не найден
        """
        return self._apis.get(identifier_key, None)

    def get_all_apis(self) -> dict[str, API]:
        """
        Возвращает словарь всех зарегистрированных API-инстансов.
        
        Returns:
            Словарь {identifier: API instance}
        """
        return self._apis

    def add_api(self, cfg: APIModel) -> None:
        """
        Добавляет новый API-инстанс в менеджер.
        
        Args:
            cfg: Конфигурация API для добавления
            
        Raises:
            RuntimeError: Если менеджер не инициализирован
            Exception: Если API с таким идентификатором уже существует
        """
        if self._stop_event is None:
            raise RuntimeError("APIManager не инициализирован: stop_event не установлен")

        identifier = cfg.identifier
        
        if identifier in self._apis:
            raise Exception(f'API с таким идентификатором уже существует: {identifier}')
        
        api = API(cfg, self._stop_event)
        self._apis[identifier] = api
        asyncio.create_task(api.worker())

    def get_identifier_matcher(self) -> IdentifierMatcher:
        """
        Возвращает экземпляр IdentifierMatcher для этого менеджера.
        
        Returns:
            IdentifierMatcher для работы с идентификаторами
        """
        return self._identifier_matcher
