"""
Тесты для config_loader.py
"""
import json
import pytest
from unittest.mock import patch, Mock, mock_open
from config_loader import load_configs


class TestConfigLoader:
    """Тесты для функции load_configs."""

    def test_load_configs_success(self):
        """Тест успешной загрузки конфигураций."""
        test_data = {
            "sources": [
                {
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
            ]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            with patch('config_loader.APIManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                result = load_configs()
                
                assert result == mock_manager
                mock_manager_class.assert_called_once_with(test_data["sources"])
                mock_manager.start.assert_called_once()

    def test_load_configs_multiple_sources(self):
        """Тест загрузки нескольких источников."""
        test_data = {
            "sources": [
                {
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
                },
                {
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
            ]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            with patch('config_loader.APIManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                result = load_configs()
                
                mock_manager_class.assert_called_once_with(test_data["sources"])
                assert len(mock_manager_class.call_args[0][0]) == 2

    def test_load_configs_empty_sources(self):
        """Тест загрузки с пустым списком источников."""
        test_data = {
            "sources": []
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            with patch('config_loader.APIManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                result = load_configs()
                
                mock_manager_class.assert_called_once_with([])
                mock_manager.start.assert_called_once()

    def test_load_configs_file_not_found(self):
        """Тест обработки отсутствующего файла."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                load_configs()

    def test_load_configs_invalid_json(self):
        """Тест обработки невалидного JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(json.JSONDecodeError):
                load_configs()

    def test_load_configs_encoding(self):
        """Тест загрузки с правильной кодировкой UTF-8."""
        test_data = {
            "sources": [
                {
                    "identifier": {
                        "url": "https://api.example.com/v1",
                        "method": "GET",
                        "extra": "тест"
                    },
                    "rate_limit": {
                        "interval": 0.1,
                        "RPD": 100,
                        "add_random": False
                    }
                }
            ]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data, ensure_ascii=False))) as mock_file:
            with patch('config_loader.APIManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                load_configs()
                
                # Проверяем, что файл открыт с правильной кодировкой
                mock_file.assert_called_once_with("apis.json", "r", encoding="utf8")

