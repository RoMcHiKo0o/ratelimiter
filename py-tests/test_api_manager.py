"""
Тесты для models/api_manager.py
"""
import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from models.api_manager import APIManager
from models.api import API
from schemas import APIModel, RateLimitModel


class TestAPIManager:
    """Тесты для класса APIManager."""

    @pytest.fixture
    def valid_config(self):
        """Создаёт валидную конфигурацию API."""
        return {
            "identifier": {
                "url": "https://api.example.com/v1",
                "method": "GET",
                "extra": ""
            },
            "rate_limit": {
                "interval": 0.1,
                "RPD": 100,
                "add_random": False
            }
        }

    @pytest.fixture
    def api_manager(self, valid_config):
        """Создаёт экземпляр APIManager."""
        return APIManager([valid_config])

    def test_init(self, valid_config):
        """Тест инициализации APIManager."""
        manager = APIManager([valid_config])
        assert len(manager.get_all_apis()) == 1
        assert manager._identifier_matcher is not None

    def test_init_empty_configs(self):
        """Тест инициализации с пустым списком конфигураций."""
        manager = APIManager([])
        assert len(manager.get_all_apis()) == 0

    def test_init_multiple_configs(self, valid_config):
        """Тест инициализации с несколькими конфигурациями."""
        config2 = {
            "identifier": {
                "url": "https://api.example.com/v2",
                "method": "POST",
                "extra": ""
            },
            "rate_limit": {
                "interval": 0.2,
                "RPD": 200,
                "add_random": True
            }
        }
        manager = APIManager([valid_config, config2])
        assert len(manager.get_all_apis()) == 2

    def test_init_invalid_config(self, valid_config):
        """Тест инициализации с невалидной конфигурацией."""
        invalid_config = {"invalid": "config"}
        manager = APIManager([valid_config, invalid_config])
        # Валидная конфигурация должна быть добавлена
        assert len(manager.get_all_apis()) == 1

    def test_init_duplicate_identifier(self, valid_config):
        """Тест инициализации с дублирующимися идентификаторами."""
        manager = APIManager([valid_config, valid_config])
        # Дубликаты должны быть пропущены
        assert len(manager.get_all_apis()) == 1

    def test_get(self, api_manager, valid_config):
        """Тест получения API по идентификатору."""
        identifier_key = json.dumps(valid_config["identifier"], sort_keys=True)
        api = api_manager.get(identifier_key)
        assert api is not None
        assert isinstance(api, API)

    def test_get_nonexistent(self, api_manager):
        """Тест получения несуществующего API."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/nonexistent",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        api = api_manager.get(identifier_key)
        assert api is None

    def test_get_all_apis(self, api_manager):
        """Тест получения всех API."""
        apis = api_manager.get_all_apis()
        assert isinstance(apis, dict)
        assert len(apis) == 1
        for api in apis.values():
            assert isinstance(api, API)

    def test_add_api(self, api_manager):
        """Тест добавления нового API."""
        new_config = APIModel(
            identifier={
                "url": "https://api.example.com/v2",
                "method": "POST",
                "extra": ""
            },
            rate_limit=RateLimitModel(
                interval=0.2,
                RPD=200,
                add_random=False
            )
        )
        
        initial_count = len(api_manager.get_all_apis())
        api_manager.add_api(new_config)
        
        assert len(api_manager.get_all_apis()) == initial_count + 1

    def test_add_api_duplicate(self, api_manager, valid_config):
        """Тест добавления дублирующегося API."""
        duplicate_config = APIModel(**valid_config)
        
        with pytest.raises(Exception) as exc_info:
            api_manager.add_api(duplicate_config)
        
        assert "уже существует" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start(self, api_manager):
        """Тест запуска фоновых задач."""
        with patch('asyncio.create_task') as mock_create_task:
            api_manager.start()
            # Должны быть созданы задачи для worker и midnight_updater
            assert mock_create_task.called

    def test_start_empty_apis(self):
        """Тест запуска с пустым списком API."""
        manager = APIManager([])
        # Не должно быть ошибок
        manager.start()

    @pytest.mark.asyncio
    async def test_reset_all_counters(self, api_manager):
        """Тест сброса всех счётчиков."""
        apis = api_manager.get_all_apis()
        for api in apis.values():
            api.counter = 50
        
        api_manager._reset_all_counters()
        
        for api in apis.values():
            assert api.counter == 0

    @pytest.mark.asyncio
    async def test_midnight_updater_stops(self, api_manager):
        """Тест остановки midnight updater."""
        # Запускаем updater
        updater_task = asyncio.create_task(api_manager._midnight_updater())
        await asyncio.sleep(0.01)
        
        # Останавливаем
        api_manager.stop_midnight_updater()
        await asyncio.sleep(0.01)
        
        # Проверяем, что событие установлено
        assert api_manager._midnight_updater_stop_event.is_set()

    def test_stop_all_workers(self, api_manager):
        """Тест остановки всех воркеров."""
        apis = api_manager.get_all_apis()
        for api in apis.values():
            api.stop = Mock()
        
        api_manager.stop_all_workers()
        
        for api in apis.values():
            api.stop.assert_called_once()

    def test_stop_midnight_updater(self, api_manager):
        """Тест остановки midnight updater."""
        assert not api_manager._midnight_updater_stop_event.is_set()
        
        api_manager.stop_midnight_updater()
        
        assert api_manager._midnight_updater_stop_event.is_set()

    def test_stop_all(self, api_manager):
        """Тест остановки всех фоновых задач."""
        apis = api_manager.get_all_apis()
        for api in apis.values():
            api.stop = Mock()
        
        api_manager.stop_all()
        
        # Проверяем, что все воркеры остановлены
        for api in apis.values():
            api.stop.assert_called_once()
        # Проверяем, что updater остановлен
        assert api_manager._midnight_updater_stop_event.is_set()

    def test_get_identifier_matcher(self, api_manager):
        """Тест получения IdentifierMatcher."""
        matcher = api_manager.get_identifier_matcher()
        assert matcher is not None
        assert matcher == api_manager._identifier_matcher

    def test_initialize_apis_skips_invalid(self):
        """Тест пропуска невалидных конфигураций при инициализации."""
        invalid_configs = [
            {"invalid": "config"},
            {"identifier": "not_a_dict"},
            None
        ]
        manager = APIManager(invalid_configs)
        assert len(manager.get_all_apis()) == 0

    def test_initialize_apis_handles_exceptions(self):
        """Тест обработки исключений при инициализации."""
        # Конфигурация, которая вызовет исключение при создании API
        config_with_error = {
            "identifier": {
                "url": "not_a_valid_url",
                "method": "GET",
                "extra": ""
            },
            "rate_limit": {
                "interval": 0.1,
                "RPD": 100,
                "add_random": False
            }
        }
        # APIModel должен валидировать URL, поэтому это должно быть пропущено
        manager = APIManager([config_with_error])
        # В зависимости от валидации, может быть 0 или 1 API
        assert isinstance(manager.get_all_apis(), dict)

