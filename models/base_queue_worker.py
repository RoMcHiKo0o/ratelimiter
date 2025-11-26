import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from logger import setup_logger

logger = setup_logger(__name__)


@dataclass(order=True)
class Item:
    """Элемент очереди запросов с приоритетом."""
    priority: int
    item: Any = field(compare=False)


class BaseQueueWorker(ABC):
    """
    Базовый класс для работы с очередью задач.
    
    Предоставляет механизм очереди с приоритетами и обработку задач в фоновом режиме.
    Дочерние классы должны реализовать метод process_task для обработки конкретных задач.
    """
    
    def __init__(self, identifier: str):
        """
        Инициализация базового обработчика очереди.
        
        Args:
            identifier: Уникальный идентификатор воркера
        """
        self.identifier = identifier
        self.queue = asyncio.PriorityQueue()
        self.stop_event = asyncio.Event()
    
    @abstractmethod
    async def process_task(self, task_data: Any) -> Any:
        """
        Абстрактный метод для обработки задачи.
        
        Дочерние классы должны реализовать этот метод для обработки конкретных задач.
        
        Args:
            task_data: Данные задачи для обработки
            
        Returns:
            Результат обработки задачи
        """
        pass
    
    @abstractmethod
    async def get_delay(self) -> float:
        """
        Абстрактный метод для получения задержки между обработкой задач.
        
        Дочерние классы должны реализовать этот метод для определения задержки.
        Если задержка не нужна, можно вернуть 0.
        
        Returns:
            Задержка в секундах (float)
        """
        pass
    
    async def worker(self):
        """
        Основной метод воркера, который обрабатывает очередь задач.
        
        Извлекает задачи из очереди, обрабатывает их через process_task
        и устанавливает результат в соответствующий Future.
        """
        logger.info(f"Worker created for {self.identifier}")
        tasks = {}

        while not self.stop_event.is_set():
            # Проверяем завершенные задачи и устанавливаем результаты
            for fut, task in list(tasks.items()):
                if task.done():
                    tasks.pop(fut)
                    try:
                        result = await task
                        fut.set_result(result)
                    except Exception as e:
                        fut.set_exception(e)
                    self.queue.task_done()

            # Обрабатываем новые задачи из очереди
            if not self.queue.empty():
                item = await self.queue.get()
                pr, (fut, task_data) = item.priority, item.item
                logger.info(
                    f"Worker {self.identifier} found task with priority {pr}")
                
                # Создаем задачу для обработки
                task = asyncio.create_task(self.process_task(task_data))
                tasks[fut] = task
                
                # Получаем задержку и ждем (если нужно)
                delay = await self.get_delay()
                if delay > 0:
                    await asyncio.sleep(delay)
            else:
                await asyncio.sleep(0)

        logger.info(f"Worker {self.identifier} завершён")
    
    async def add_task(self, task_data: Any, priority: int = 0) -> asyncio.Future:
        """
        Добавляет задачу в очередь.
        
        Args:
            task_data: Данные задачи для обработки
            priority: Приоритет задачи (меньше = выше приоритет)
            
        Returns:
            Future объект, в который будет установлен результат обработки задачи
        """
        fut = asyncio.Future()
        item = Item(priority, (fut, task_data))
        await self.queue.put(item)
        return fut
    
    def stop(self):
        """
        Останавливает воркера, устанавливая stop_event.
        
        После вызова этого метода воркер завершит обработку текущих задач и остановится.
        """
        self.stop_event.set()
        logger.info(f"Stop event set for worker {self.identifier}")

