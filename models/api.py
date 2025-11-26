import asyncio
from random import random
from typing import Any

from schemas import APIModel
from services.requester import make_request
from models.base_queue_worker import BaseQueueWorker

from logger import setup_logger

logger = setup_logger(__name__)


class API(BaseQueueWorker):
    def __init__(self, config: APIModel):
        super().__init__(config.identifier)
        self._interval = config.rate_limit.interval * 1.1
        self.counter = 0
        self.rpd = config.rate_limit.RPD
        self.add_random = config.rate_limit.add_random

    @property
    def interval(self):
        return self._interval + (random() if self.add_random else 0)

    async def process_task(self, task_data: dict) -> Any:
        """
        Обрабатывает HTTP запрос через make_request.
        
        Args:
            task_data: Словарь с данными запроса (url, method, headers, params, json)
            
        Returns:
            Результат выполнения запроса
        """
        logger.info(
            f"Worker {self.identifier} processing task: {task_data.get('method')}, {task_data.get('url')}")
        return await make_request(task_data)

    async def get_delay(self) -> float:
        """
        Возвращает задержку между обработкой запросов.
        
        Returns:
            Задержка в секундах с учетом случайного значения (если включено)
        """
        return self.interval
