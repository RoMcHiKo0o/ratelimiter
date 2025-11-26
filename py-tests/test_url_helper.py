"""
Тесты для services/url_helper.py
"""
import pytest
from services.url_helper import URLHelper


class TestURLHelper:
    """Тесты для класса URLHelper."""

    def test_get_sub_urls_basic(self):
        """Тест получения подпутей для простого URL."""
        url = "https://api.example.com/v1/users/123"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        expected = [
            "https://api.example.com/v1",
            "https://api.example.com/v1/users",
            "https://api.example.com/v1/users/123"
        ]
        assert result == expected

    def test_get_sub_urls_single_path(self):
        """Тест получения подпутей для URL с одним путём."""
        url = "https://api.example.com/v1"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        expected = ["https://api.example.com/v1"]
        assert result == expected

    def test_get_sub_urls_root(self):
        """Тест получения подпутей для корневого URL."""
        url = "https://api.example.com/"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        assert result == []

    def test_get_sub_urls_no_path(self):
        """Тест получения подпутей для URL без пути."""
        url = "https://api.example.com"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        assert result == []

    def test_get_sub_urls_multiple_segments(self):
        """Тест получения подпутей для URL с несколькими сегментами."""
        url = "https://api.example.com/api/v1/users/123/posts/456"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        expected = [
            "https://api.example.com/api",
            "https://api.example.com/api/v1",
            "https://api.example.com/api/v1/users",
            "https://api.example.com/api/v1/users/123",
            "https://api.example.com/api/v1/users/123/posts",
            "https://api.example.com/api/v1/users/123/posts/456"
        ]
        assert result == expected

    def test_get_sub_urls_with_query(self):
        """Тест получения подпутей для URL с query параметрами."""
        url = "https://api.example.com/v1/users?page=1"
        helper = URLHelper()
        result = helper.get_sub_urls(url)
        
        # Query параметры не должны влиять на пути
        expected = [
            "https://api.example.com/v1",
            "https://api.example.com/v1/users"
        ]
        assert result == expected

    def test_find_matching_sub_url_exact_match(self):
        """Тест поиска точного совпадения URL."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users/123"
        identifier_url = "https://api.example.com/v1/users/123"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result == identifier_url

    def test_find_matching_sub_url_partial_match(self):
        """Тест поиска частичного совпадения URL."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users/123"
        identifier_url = "https://api.example.com/v1/users"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result == identifier_url

    def test_find_matching_sub_url_base_match(self):
        """Тест поиска совпадения с базовым путём."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users/123"
        identifier_url = "https://api.example.com/v1"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result == identifier_url

    def test_find_matching_sub_url_no_match(self):
        """Тест поиска совпадения когда совпадений нет."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users/123"
        identifier_url = "https://api.example.com/v2/posts"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result is None

    def test_find_matching_sub_url_most_specific(self):
        """Тест поиска наиболее специфичного совпадения."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users/123"
        # Идентификатор должен совпасть с более специфичным путём
        identifier_url = "https://api.example.com/v1/users"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result == identifier_url

    def test_find_matching_sub_url_different_domains(self):
        """Тест поиска совпадения для разных доменов."""
        helper = URLHelper()
        request_url = "https://api.example.com/v1/users"
        identifier_url = "https://api.other.com/v1/users"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result is None

    def test_find_matching_sub_url_empty_paths(self):
        """Тест поиска совпадения для пустых путей."""
        helper = URLHelper()
        request_url = "https://api.example.com"
        identifier_url = "https://api.example.com"
        
        result = helper.find_matching_sub_url(request_url, identifier_url)
        assert result == identifier_url

