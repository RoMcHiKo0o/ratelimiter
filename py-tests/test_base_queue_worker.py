"""
Тесты для models/base_queue_worker.py
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock
from models.base_queue_worker import BaseQueueWorker, Item


class ConcreteWorker(BaseQueueWorker):
    """Конкретная реализация BaseQueueWorker для тестирования."""
    
    def __init__(self, identifier: str, process_delay: float = 0.0):
        super().__init__(identifier)
        self.process_delay = process_delay
        self.processed_tasks = []
    
    async def process_task(self, task_data):
        """Обработка задачи."""
        await asyncio.sleep(self.process_delay)
        self.processed_tasks.append(task_data)
        return f"processed_{task_data}"
    
    async def get_delay(self) -> float:
        """Возвращает задержку."""
        return 0.0


class TestItem:
    """Тесты для класса Item."""

    def test_item_creation(self):
        """Тест создания элемента очереди."""
        item = Item(priority=1, item="test_data")
        assert item.priority == 1
        assert item.item == "test_data"

    def test_item_ordering(self):
        """Тест сортировки элементов по приоритету."""
        item1 = Item(priority=1, item="data1")
        item2 = Item(priority=2, item="data2")
        item3 = Item(priority=1, item="data3")
        
        assert item1 < item2
        assert item1 <= item3
        assert item2 > item1


class TestBaseQueueWorker:
    """Тесты для класса BaseQueueWorker."""

    def test_init(self):
        """Тест инициализации воркера."""
        worker = ConcreteWorker("test_worker")
        assert worker.identifier == "test_worker"
        assert worker.queue is not None
        assert worker.stop_event is not None
        assert not worker.stop_event.is_set()

    @pytest.mark.asyncio
    async def test_add_task(self):
        """Тест добавления задачи в очередь."""
        worker = ConcreteWorker("test_worker")
        task_data = {"test": "data"}
        
        future = await worker.add_task(task_data, priority=1)
        
        assert future is not None
        assert isinstance(future, asyncio.Future)
        assert not worker.queue.empty()

    @pytest.mark.asyncio
    async def test_add_task_priority(self):
        """Тест добавления задач с разными приоритетами."""
        worker = ConcreteWorker("test_worker")
        
        future1 = await worker.add_task("task1", priority=2)
        future2 = await worker.add_task("task2", priority=1)
        future3 = await worker.add_task("task3", priority=3)
        
        # Задачи должны быть извлечены в порядке приоритета
        item1 = await worker.queue.get()
        item2 = await worker.queue.get()
        item3 = await worker.queue.get()
        
        assert item1.priority == 1  # Наивысший приоритет
        assert item2.priority == 2
        assert item3.priority == 3

    @pytest.mark.asyncio
    async def test_stop(self):
        """Тест остановки воркера."""
        worker = ConcreteWorker("test_worker")
        assert not worker.stop_event.is_set()
        
        worker.stop()
        
        assert worker.stop_event.is_set()

    @pytest.mark.asyncio
    async def test_worker_processes_tasks(self):
        """Тест обработки задач воркером."""
        worker = ConcreteWorker("test_worker", process_delay=0.01)
        task_data = {"test": "data"}
        
        # Запускаем воркер в фоне
        worker_task = asyncio.create_task(worker.worker())
        
        # Даём время на запуск
        await asyncio.sleep(0.01)
        
        # Добавляем задачу
        future = await worker.add_task(task_data)
        
        # Ждём обработки
        await asyncio.sleep(0.1)
        
        # Останавливаем воркер
        worker.stop()
        await asyncio.sleep(0.01)
        
        # Проверяем результаты
        assert len(worker.processed_tasks) == 1
        assert worker.processed_tasks[0] == task_data
        assert future.done()
        result = await future
        assert result == f"processed_{task_data}"

    @pytest.mark.asyncio
    async def test_worker_stops_on_stop_event(self):
        """Тест остановки воркера по событию."""
        worker = ConcreteWorker("test_worker")
        
        # Запускаем воркер
        worker_task = asyncio.create_task(worker.worker())
        await asyncio.sleep(0.01)
        
        # Останавливаем
        worker.stop()
        await asyncio.sleep(0.01)
        
        # Проверяем, что воркер остановился
        assert worker_task.done() or worker.stop_event.is_set()

    @pytest.mark.asyncio
    async def test_worker_handles_exception(self):
        """Тест обработки исключений в задачах."""
        class FailingWorker(ConcreteWorker):
            async def process_task(self, task_data):
                raise ValueError("Test error")
        
        worker = FailingWorker("test_worker")
        worker_task = asyncio.create_task(worker.worker())
        await asyncio.sleep(0.01)
        
        future = await worker.add_task("test")
        await asyncio.sleep(0.1)
        
        worker.stop()
        await asyncio.sleep(0.01)
        
        # Проверяем, что исключение установлено в Future
        assert future.done()
        with pytest.raises(ValueError):
            await future

    @pytest.mark.asyncio
    async def test_worker_multiple_tasks(self):
        """Тест обработки нескольких задач."""
        worker = ConcreteWorker("test_worker", process_delay=0.01)
        worker_task = asyncio.create_task(worker.worker())
        await asyncio.sleep(0.01)
        
        futures = []
        for i in range(3):
            future = await worker.add_task(f"task_{i}")
            futures.append(future)
        
        await asyncio.sleep(0.2)
        worker.stop()
        await asyncio.sleep(0.01)
        
        assert len(worker.processed_tasks) == 3
        for i, future in enumerate(futures):
            assert future.done()
            result = await future
            assert result == f"processed_task_{i}"

    @pytest.mark.asyncio
    async def test_worker_with_delay(self):
        """Тест воркера с задержкой между задачами."""
        class DelayedWorker(ConcreteWorker):
            async def get_delay(self) -> float:
                return 0.05
        
        worker = DelayedWorker("test_worker", process_delay=0.01)
        worker_task = asyncio.create_task(worker.worker())
        await asyncio.sleep(0.01)
        
        future1 = await worker.add_task("task1")
        await asyncio.sleep(0.01)
        future2 = await worker.add_task("task2")
        
        await asyncio.sleep(0.2)
        worker.stop()
        await asyncio.sleep(0.01)
        
        # Обе задачи должны быть обработаны
        assert len(worker.processed_tasks) == 2

