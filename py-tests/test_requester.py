"""
Тесты для services/requester.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.responses import JSONResponse
from services.requester import make_request


class TestRequester:
    """Тесты для функции make_request."""

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Тест успешного выполнения запроса."""
        mock_response_data = {"status": "ok", "data": "test"}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "application/json",
            "X-Custom-Header": "value",
            "Content-Length": "100",
            "Content-Encoding": "gzip"
        }
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        with patch('services.requester.aiohttp.ClientSession', return_value=mock_session):
            request_data = {
                "url": "https://api.example.com/test",
                "method": "GET"
            }
            result = await make_request(request_data)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200
        assert result.body is not None
        # Проверяем, что фильтрованные заголовки не содержат исключённые
        assert "Content-Length" not in result.headers
        assert "Content-Encoding" not in result.headers
        assert "X-Custom-Header" in result.headers

    @pytest.mark.asyncio
    async def test_make_request_with_error(self):
        """Тест обработки ошибки при запросе."""
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(side_effect=Exception("Connection error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        with patch('services.requester.aiohttp.ClientSession', return_value=mock_session):
            request_data = {
                "url": "https://api.example.com/test",
                "method": "GET"
            }
            result = await make_request(request_data)
        
        assert isinstance(result, JSONResponse)
        assert "error" in result.body.decode()
        assert "Exception" in result.body.decode() or "Connection error" in result.body.decode()

    @pytest.mark.asyncio
    async def test_make_request_filters_headers(self):
        """Тест фильтрации заголовков."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Type": "application/json",
            "Content-Length": "100",
            "Content-Encoding": "gzip",
            "Transfer-Encoding": "chunked",
            "X-Custom": "value"
        }
        mock_response.json = AsyncMock(return_value={})
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        with patch('services.requester.aiohttp.ClientSession', return_value=mock_session):
            request_data = {
                "url": "https://api.example.com/test",
                "method": "GET"
            }
            result = await make_request(request_data)
        
        # Проверяем, что исключённые заголовки отсутствуют
        assert "Content-Length" not in result.headers
        assert "Content-Encoding" not in result.headers
        assert "Transfer-Encoding" not in result.headers
        # Проверяем, что другие заголовки присутствуют
        assert "X-Custom" in result.headers

    @pytest.mark.asyncio
    async def test_make_request_with_all_params(self):
        """Тест запроса со всеми параметрами."""
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.headers = {}
        mock_response.json = AsyncMock(return_value={"created": True})
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        with patch('services.requester.aiohttp.ClientSession', return_value=mock_session):
            request_data = {
                "url": "https://api.example.com/test",
                "method": "POST",
                "headers": {"Authorization": "Bearer token"},
                "params": {"page": 1},
                "json": {"name": "test"}
            }
            result = await make_request(request_data)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        # Проверяем, что request был вызван с правильными параметрами
        mock_session.request.assert_called_once()
        call_kwargs = mock_session.request.call_args[1]
        assert call_kwargs["url"] == request_data["url"]
        assert call_kwargs["method"] == request_data["method"]
        assert call_kwargs["headers"] == request_data["headers"]
        assert call_kwargs["params"] == request_data["params"]
        assert call_kwargs["json"] == request_data["json"]

    @pytest.mark.asyncio
    async def test_make_request_json_decode_error(self):
        """Тест обработки ошибки декодирования JSON."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        with patch('services.requester.aiohttp.ClientSession', return_value=mock_session):
            request_data = {
                "url": "https://api.example.com/test",
                "method": "GET"
            }
            result = await make_request(request_data)
        
        assert isinstance(result, JSONResponse)
        assert "error" in result.body.decode()

