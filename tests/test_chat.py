"""Unit tests for chat endpoint and service."""

import os
import sys

# Set up environment variables before any imports
os.environ['YANDEX_CLOUD_FOLDER'] = 'test-folder-id'
os.environ['YANDEX_CLOUD_API_KEY'] = 'test-api-key'
os.environ['YANDEX_CLOUD_MODEL'] = 'deepseek-v4-flash/latest'
os.environ['APP_ENV'] = 'test'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

# Clear cached imports to reload with new env vars
for module_name in list(sys.modules.keys()):
    if 'llm' in module_name or 'services' in module_name or 'api' in module_name:
        del sys.modules[module_name]

import pytest
import socket
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from api.models import ChatRequest, ChatResponse
from services.chat import ChatService
from cache.redis_client import CacheClient, InMemoryCache


class TestChatService:
    """Tests for ChatService class."""

    def test_init_default(self):
        """Test ChatService initialization with defaults."""
        service = ChatService()
        assert service.client is not None
        assert service.settings is None
        assert service.cache is not None
        assert service.cache_ttl == 600

    def test_init_custom(self):
        """Test ChatService initialization with custom dependencies."""
        mock_client = Mock()
        mock_settings = Mock()
        mock_cache = Mock()
        
        service = ChatService(client=mock_client, settings=mock_settings, cache_client=mock_cache)
        assert service.client == mock_client
        assert service.settings == mock_settings
        assert service.cache == mock_cache

    def test_generate_cache_key(self):
        """Test cache key generation."""
        service = ChatService()
        request = ChatRequest(message="test message")
        
        key = service._generate_cache_key(request, temperature=0.5, max_output_tokens=1000)
        
        assert key.startswith("chat:")
        assert len(key) == 37

    def test_check_network_available(self):
        """Test network check when network is available."""
        service = ChatService()
        
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.return_value = None
            result = service._check_network(timeout=1)
            
            assert result is True

    def test_check_network_unavailable(self):
        """Test network check when network is unavailable."""
        service = ChatService()
        
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = socket.error()
            result = service._check_network(timeout=1)
            
            assert result is False

    def test_parse_llm_response_json(self):
        """Test parsing LLM response as JSON."""
        service = ChatService()
        response = '{"model": "Toyota", "price": 50000}'
        
        parsed = service._parse_llm_response(response)
        
        assert parsed['model'] == 'Toyota'
        assert parsed['price'] == 50000.0

    def test_create_fallback_response(self):
        """Test fallback response creation."""
        service = ChatService()
        
        fallback = service._create_fallback_response("Network error")
        
        assert fallback.model == "Ошибка"
        assert fallback.price == 0.0

    def test_process_request_cache_hit(self):
        """Test processing request with cache hit."""
        service = ChatService()
        request = ChatRequest(message="test message")
        
        cached_data = {"message": "test message", "model": "Toyota", "price": 50000}
        
        with patch.object(service.cache, 'get', return_value=cached_data) as mock_get:
            response = service.process_request(request)
            
            assert response.model == "Toyota"
            assert response.price == 50000.0
            mock_get.assert_called_once()

class TestChatEndpoint:
    """Tests for chat endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_chat_endpoint_success(self, client):
        """Test successful chat endpoint request."""
        request_data = {"message": "Какая стоимость КАСКО для Toyota 230 лс?"}
        
        mock_response = ChatResponse(
            model="Toyota",
            price=50000
        )
        
        with patch('services.chat.chat_service.process_request', return_value=mock_response):
            response = client.post("/chat/", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data['model'] == "Toyota"
            assert data['price'] == 50000

    def test_chat_endpoint_empty_message(self, client):
        """Test chat endpoint with empty message."""
        request_data = {"message": ""}
        
        response = client.post("/chat/", json=request_data)
        
        assert response.status_code == 422

    def test_chat_endpoint_message_too_long(self, client):
        """Test chat endpoint with message too long."""
        request_data = {"message": "x" * 1001}
        
        response = client.post("/chat/", json=request_data)
        
        assert response.status_code == 422

    def test_chat_endpoint_validation_error(self, client):
        """Test chat endpoint with missing message."""
        request_data = {}
        
        response = client.post("/chat/", json=request_data)
        
        assert response.status_code == 422

    def test_chat_endpoint_llm_error(self, client):
        """Test chat endpoint with LLM error."""
        request_data = {"message": "test message"}
        
        with patch('services.chat.chat_service.process_request', side_effect=Exception("LLM Error")):
            response = client.post("/chat/", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "LLM Error" in data['detail']


class TestCacheClient:
    """Tests for CacheClient class."""

    def test_get_nonexistent_key(self):
        """Test getting nonexistent key."""
        cache = CacheClient()
        
        result = cache.get("nonexistent_key")
        
        assert result is None

    def test_set_and_get(self):
        """Test setting and getting value."""
        cache = CacheClient()
        
        cache.set("test_key", {"model": "Toyota", "price": 50000}, ttl=60)
        result = cache.get("test_key")
        
        assert result is not None
        assert result['model'] == "Toyota"
        assert result['price'] == 50000

    def test_exists_key(self):
        """Test checking if key exists."""
        cache = CacheClient()
        
        cache.set("exists_key", {"test": "value"})
        result = cache.exists("exists_key")
        
        assert result is True

    def test_exists_nonexistent_key(self):
        """Test checking if nonexistent key exists."""
        cache = CacheClient()
        
        result = cache.exists("nonexistent_key")
        
        assert result is False

    def test_delete_key(self):
        """Test deleting key."""
        cache = CacheClient()
        
        cache.set("delete_key", {"test": "value"})
        cache.delete("delete_key")
        result = cache.exists("delete_key")
        
        assert result is False


class TestInMemoryCache:
    """Tests for InMemoryCache class."""

    def test_get_nonexistent(self):
        """Test getting nonexistent key from in-memory cache."""
        cache = InMemoryCache()
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_set_and_get(self):
        """Test setting and getting value."""
        cache = InMemoryCache()
        
        cache.set("key", {"test": "value"})
        result = cache.get("key")
        
        assert result is not None

    def test_exists(self):
        """Test checking if key exists."""
        cache = InMemoryCache()
        
        cache.set("key", {"test": "value"})
        result = cache.exists("key")
        
        assert result is True

    def test_delete(self):
        """Test deleting key."""
        cache = InMemoryCache()
        
        cache.set("key", {"test": "value"})
        cache.delete("key")
        result = cache.exists("key")
        
        assert result is False
