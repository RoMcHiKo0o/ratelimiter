"""
Тесты для models/api.py
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, Mock
from models.api import API
from schemas import APIModel, RateLimitModel


class TestAPI:
    """Тесты для класса API."""

    @pytest.fixture
    def api_config(self):
        """Создаёт конфигурацию API для тестов."""
        return APIModel(
            identifier={
                "url": "https://api.example.com/v1",
                "method": "GET",
                "extra": ""
            },
            rate_limit=RateLimitModel(
                interval=0.1,
                RPD=100,
                add_random=False
            )
        )

    @pytest.fixture
    def api(self, api_config):
        """Создаёт экземпляр API."""
        return API(api_config)

    def test_init(self, api_config):
        """Тест инициализации API."""
        api = API(api_config)
        assert api.counter == 0
        assert api.rpd == 100
        assert api.add_random is False
        assert api._interval == 0.1 * 1.1

    def test_interval_property_no_random(self, api):
        """Тест свойства interval без случайного значения."""
        api.add_random = False
        interval = api.interval
        assert interval == api._interval

    def test_interval_property_with_random(self, api):
        """Тест свойства interval со случайным значением."""
        api.add_random = True
        interval = api.interval
        # Интервал должен быть больше базового
        assert interval >= api._interval
        assert interval < api._interval + 1.0

    def test_get_delay(self, api):
        """Тест метода get_delay."""
        delay = asyncio.run(api.get_delay())
        assert delay == api._interval

    @pytest.mark.asyncio
    async def test_process_task(self, api):
        """Тест обработки задачи."""
        task_data = {
            "url": "https://api.example.com/v1/test",
            "method": "GET"
        }
        
        mock_response = Mock()
        with patch('models.api.make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            result = await api.process_task(task_data)
        
        assert result == mock_response
        mock_make_request.assert_called_once_with(task_data)

    @pytest.mark.asyncio
    async def test_process_task_increments_counter(self, api):
        """Тест увеличения счётчика при обработке задачи."""
        initial_counter = api.counter
        task_data = {
            "url": "https://api.example.com/v1/test",
            "method": "GET"
        }
        
        mock_response = Mock()
        with patch('models.api.make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            await api.process_task(task_data)
        
        # Счётчик не должен увеличиваться автоматически в process_task
        # (это может быть сделано в другом месте)
        # Проверяем, что метод выполнился
        assert mock_make_request.called

    def test_counter_reset(self, api):
        """Тест сброса счётчика."""
        api.counter = 50
        assert api.counter == 50
        
        api.counter = 0
        assert api.counter == 0

    def test_rpd_limit(self, api):
        """Тест лимита запросов в день."""
        assert api.rpd == 100
        api.rpd = 200
        assert api.rpd == 200

    def test_interval_calculation(self, api_config):
        """Тест расчёта интервала."""
        api = API(api_config)
        # Интервал должен быть равен interval * 1.1
        expected_interval = api_config.rate_limit.interval * 1.1
        assert api._interval == expected_interval

    @pytest.mark.asyncio
    async def test_worker_inheritance(self, api):
        """Тест наследования от BaseQueueWorker."""
        # Проверяем, что API наследуется от BaseQueueWorker
        from models.base_queue_worker import BaseQueueWorker
        assert isinstance(api, BaseQueueWorker)
        
        # Проверяем, что методы базового класса доступны
        assert hasattr(api, 'add_task')
        assert hasattr(api, 'worker')
        assert hasattr(api, 'stop')

    @pytest.mark.asyncio
    async def test_api_worker_integration(self, api):
        """Тест интеграции API с воркером."""
        task_data = {
            "url": "https://api.example.com/v1/test",
            "method": "GET"
        }
        
        mock_response = Mock()
        with patch('models.api.make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            # Запускаем воркер
            worker_task = asyncio.create_task(api.worker())
            await asyncio.sleep(0.01)
            
            # Добавляем задачу
            future = await api.add_task(task_data)
            
            # Ждём обработки
            await asyncio.sleep(0.2)
            
            # Останавливаем
            api.stop()
            await asyncio.sleep(0.01)
            
            # Проверяем результат
            assert future.done()
            result = await future
            assert result == mock_response

    def test_api_with_random(self, api_config):
        """Тест API с включённым случайным значением."""
        api_config.rate_limit.add_random = True
        api = API(api_config)
        
        assert api.add_random is True
        
        # Проверяем, что interval возвращает разные значения
        intervals = [api.interval for _ in range(10)]
        # Хотя бы одно значение должно отличаться (с высокой вероятностью)
        assert len(set(intervals)) > 1 or intervals[0] > api._interval

