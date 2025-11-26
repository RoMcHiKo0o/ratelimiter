"""
Тесты для services/identifier_matcher.py
"""
import json
import pytest
from unittest.mock import Mock, MagicMock
from services.identifier_matcher import IdentifierMatcher


class TestIdentifierMatcher:
    """Тесты для класса IdentifierMatcher."""

    @pytest.fixture
    def mock_api_manager(self):
        """Создаёт мок APIManager."""
        manager = Mock()
        manager.get_all_apis.return_value = {}
        return manager

    @pytest.fixture
    def identifier_matcher(self, mock_api_manager):
        """Создаёт экземпляр IdentifierMatcher."""
        return IdentifierMatcher(mock_api_manager)

    def test_init(self, mock_api_manager):
        """Тест инициализации IdentifierMatcher."""
        matcher = IdentifierMatcher(mock_api_manager)
        assert matcher._api_manager == mock_api_manager
        assert matcher._url_helper is not None

    def test_find_identifier_no_apis(self, identifier_matcher):
        """Тест поиска идентификатора когда нет API."""
        result = identifier_matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="GET",
            extra=""
        )
        assert result is None

    def test_find_identifier_exact_match(self, mock_api_manager):
        """Тест поиска точного совпадения идентификатора."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="GET",
            extra=""
        )
        
        assert result is not None
        assert result["url"] == "https://api.example.com/v1/users"
        assert result["method"] == "GET"
        assert result["extra"] == ""

    def test_find_identifier_any_method(self, mock_api_manager):
        """Тест поиска идентификатора с методом ANY."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "ANY",
            "extra": ""
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="POST",
            extra=""
        )
        
        assert result is not None
        assert result["method"] == "ANY"

    def test_find_identifier_with_extra(self, mock_api_manager):
        """Тест поиска идентификатора с extra параметром."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": "test_extra"
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="GET",
            extra="test_extra"
        )
        
        assert result is not None
        assert result["extra"] == "test_extra"

    def test_find_identifier_wrong_extra(self, mock_api_manager):
        """Тест поиска идентификатора с неправильным extra."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": "test_extra"
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="GET",
            extra="wrong_extra"
        )
        
        assert result is None

    def test_find_identifier_wrong_method(self, mock_api_manager):
        """Тест поиска идентификатора с неправильным методом."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="POST",
            extra=""
        )
        
        assert result is None

    def test_find_identifier_multiple_matches(self, mock_api_manager):
        """Тест поиска нескольких совпадений."""
        identifier_key1 = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        identifier_key2 = json.dumps({
            "url": "https://api.example.com/v1",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        mock_api1 = Mock()
        mock_api2 = Mock()
        mock_api_manager.get_all_apis.return_value = {
            identifier_key1: mock_api1,
            identifier_key2: mock_api2
        }
        
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.find_identifier(
            url="https://api.example.com/v1/users",
            method="GET",
            extra="",
            first_match_only=False
        )
        
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_check_conflict_no_conflicts(self, mock_api_manager):
        """Тест проверки конфликтов когда их нет."""
        mock_api_manager.get_all_apis.return_value = {}
        
        matcher = IdentifierMatcher(mock_api_manager)
        identifier_str = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        result = matcher.check_conflict(identifier_str)
        assert result == []

    def test_check_conflict_has_conflicts(self, mock_api_manager):
        """Тест проверки конфликтов когда они есть."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        identifier_str = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        result = matcher.check_conflict(identifier_str)
        assert len(result) > 0

    def test_check_conflict_invalid_json(self, mock_api_manager):
        """Тест проверки конфликтов с невалидным JSON."""
        matcher = IdentifierMatcher(mock_api_manager)
        result = matcher.check_conflict("invalid json")
        assert result == []

    def test_has_conflict_true(self, mock_api_manager):
        """Тест has_conflict когда есть конфликты."""
        identifier_key = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        mock_api = Mock()
        mock_api_manager.get_all_apis.return_value = {identifier_key: mock_api}
        
        matcher = IdentifierMatcher(mock_api_manager)
        identifier_str = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        result = matcher.has_conflict(identifier_str)
        assert result is True

    def test_has_conflict_false(self, mock_api_manager):
        """Тест has_conflict когда конфликтов нет."""
        mock_api_manager.get_all_apis.return_value = {}
        
        matcher = IdentifierMatcher(mock_api_manager)
        identifier_str = json.dumps({
            "url": "https://api.example.com/v1/users",
            "method": "GET",
            "extra": ""
        }, sort_keys=True)
        
        result = matcher.has_conflict(identifier_str)
        assert result is False

    def test_matches_extra_true(self):
        """Тест _matches_extra когда extra совпадает."""
        identifier_dict = {"extra": "test"}
        result = IdentifierMatcher._matches_extra(identifier_dict, "test")
        assert result is True

    def test_matches_extra_false(self):
        """Тест _matches_extra когда extra не совпадает."""
        identifier_dict = {"extra": "test"}
        result = IdentifierMatcher._matches_extra(identifier_dict, "other")
        assert result is False

    def test_matches_extra_empty(self):
        """Тест _matches_extra с пустым extra."""
        identifier_dict = {"extra": ""}
        result = IdentifierMatcher._matches_extra(identifier_dict, "")
        assert result is True

    def test_matches_method_exact(self):
        """Тест _matches_method с точным совпадением."""
        identifier_dict = {"method": "GET"}
        result = IdentifierMatcher._matches_method(identifier_dict, "GET", True)
        assert result is True

    def test_matches_method_any_in_identifier(self):
        """Тест _matches_method когда идентификатор имеет метод ANY."""
        identifier_dict = {"method": "ANY"}
        result = IdentifierMatcher._matches_method(identifier_dict, "POST", True)
        assert result is True

    def test_matches_method_any_in_request(self):
        """Тест _matches_method когда запрос имеет метод ANY."""
        identifier_dict = {"method": "GET"}
        result = IdentifierMatcher._matches_method(identifier_dict, "ANY", False)
        assert result is True

    def test_matches_method_no_match(self):
        """Тест _matches_method когда методы не совпадают."""
        identifier_dict = {"method": "GET"}
        result = IdentifierMatcher._matches_method(identifier_dict, "POST", True)
        assert result is False

