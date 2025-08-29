"""Tests for AI client functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import aiohttp

from src.utils.ai_client import (
    OpenRouterClient, MultiLLMClient, ChatMessage, AIResponse
)
from src.utils.config import ConfigManager


class TestChatMessage:
    """Test ChatMessage data class."""
    
    def test_chat_message_creation(self):
        """Test creating ChatMessage."""
        message = ChatMessage(role="user", content="Hello, world!")
        
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp is None
    
    def test_chat_message_with_timestamp(self):
        """Test ChatMessage with timestamp."""
        timestamp = datetime.now()
        message = ChatMessage(role="assistant", content="Hi there!", timestamp=timestamp)
        
        assert message.role == "assistant"
        assert message.content == "Hi there!"
        assert message.timestamp == timestamp


class TestAIResponse:
    """Test AIResponse data class."""
    
    def test_ai_response_creation(self):
        """Test creating AIResponse."""
        timestamp = datetime.now()
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        response = AIResponse(
            content="Generated content",
            model="test-model",
            usage=usage,
            timestamp=timestamp,
            cost_estimate=0.001
        )
        
        assert response.content == "Generated content"
        assert response.model == "test-model"
        assert response.usage == usage
        assert response.timestamp == timestamp
        assert response.cost_estimate == 0.001


class TestOpenRouterClient:
    """Test OpenRouterClient functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration manager."""
        config = Mock(spec=ConfigManager)
        config.get_config.side_effect = lambda key, default=None: {
            'openrouter_api_key': 'test-api-key',
            'fallback_models': [
                'anthropic/claude-3-sonnet-20240229',
                'openai/gpt-4-turbo'
            ],
            'max_retries': 3,
            'timeout': 30,
            'temperature': 0.7,
            'max_tokens': 4000
        }.get(key, default)
        return config
    
    @pytest.fixture
    def client(self, mock_config):
        """Create OpenRouterClient with mock config."""
        return OpenRouterClient(mock_config)
    
    def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = OpenRouterClient(mock_config)
        
        assert client.api_key == 'test-api-key'
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert len(client.fallback_models) == 2
        assert client.max_retries == 3
        assert client.timeout == 30
    
    def test_client_without_api_key(self):
        """Test client initialization without API key."""
        config = Mock(spec=ConfigManager)
        config.get_config.return_value = None
        
        client = OpenRouterClient(config)
        assert client.api_key is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager functionality."""
        async with client as c:
            assert c is client
            assert c.session is not None
        
        # Session should be closed after context
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_generate_response_without_api_key(self, mock_config):
        """Test generate_response without API key."""
        mock_config.get_config.side_effect = lambda key, default=None: {
            'openrouter_api_key': None,
            'fallback_models': ['test-model']
        }.get(key, default)
        
        client = OpenRouterClient(mock_config)
        messages = [ChatMessage(role="user", content="Test")]
        
        with pytest.raises(ValueError, match="OpenRouter API key not configured"):
            await client.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_successful_generate_response(self, client):
        """Test successful response generation."""
        messages = [ChatMessage(role="user", content="Hello")]
        
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Hello! How can I help you today?"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            response = await client.generate_response(messages)
            
            assert isinstance(response, AIResponse)
            assert response.content == "Hello! How can I help you today?"
            assert response.usage["total_tokens"] == 25
            assert response.cost_estimate > 0
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, client):
        """Test fallback to different models."""
        messages = [ChatMessage(role="user", content="Test")]
        
        mock_response_data = {
            "choices": [{"message": {"content": "Fallback response"}}],
            "usage": {"total_tokens": 10}
        }
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            # First model fails, second succeeds
            mock_request.side_effect = [Exception("First model failed"), mock_response_data]
            
            response = await client.generate_response(messages)
            
            assert response.content == "Fallback response"
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_all_models_fail(self, client):
        """Test when all fallback models fail."""
        messages = [ChatMessage(role="user", content="Test")]
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("All models failed")
            
            with pytest.raises(Exception, match="All AI models failed"):
                await client.generate_response(messages)
    
    def test_cost_estimation(self, client):
        """Test cost estimation for different models."""
        usage = {"total_tokens": 1000}
        
        # Test known model
        cost1 = client._estimate_cost(usage, "anthropic/claude-3-sonnet-20240229")
        assert cost1 > 0
        
        # Test unknown model (should use default)
        cost2 = client._estimate_cost(usage, "unknown/model")
        assert cost2 > 0
        
        # Cost should be proportional to tokens
        usage_double = {"total_tokens": 2000}
        cost_double = client._estimate_cost(usage_double, "anthropic/claude-3-sonnet-20240229")
        assert cost_double == cost1 * 2
    
    def test_usage_stats_tracking(self, client):
        """Test usage statistics tracking."""
        # Initially empty
        stats = client.get_usage_stats()
        assert stats['total_requests'] == 0
        assert stats['total_tokens'] == 0
        assert stats['estimated_cost'] == 0.0
        
        # Simulate usage tracking
        client.total_tokens_used = 1000
        client.total_cost = 0.05
        client.request_count = 5
        
        stats = client.get_usage_stats()
        assert stats['total_requests'] == 5
        assert stats['total_tokens'] == 1000
        assert stats['estimated_cost'] == 0.05
        assert stats['average_tokens_per_request'] == 200
    
    def test_reset_usage_stats(self, client):
        """Test resetting usage statistics."""
        client.total_tokens_used = 1000
        client.total_cost = 0.05
        client.request_count = 5
        
        client.reset_usage_stats()
        
        stats = client.get_usage_stats()
        assert stats['total_requests'] == 0
        assert stats['total_tokens'] == 0
        assert stats['estimated_cost'] == 0.0


class TestOpenRouterClientHTTP:
    """Test HTTP-specific functionality."""
    
    @pytest.fixture
    def client(self):
        """Create client with test config."""
        config = Mock(spec=ConfigManager)
        config.get_config.side_effect = lambda key, default=None: {
            'openrouter_api_key': 'test-key',
            'max_retries': 2,
            'temperature': 0.8,
            'max_tokens': 2000
        }.get(key, default)
        return OpenRouterClient(config)
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client):
        """Test successful HTTP request."""
        messages = [ChatMessage(role="user", content="Test")]
        model = "test-model"
        
        mock_response_data = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 20}
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        client.session = mock_session
        
        result = await client._make_request(messages, model)
        assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_make_request_auth_error(self, client):
        """Test authentication error handling."""
        messages = [ChatMessage(role="user", content="Test")]
        model = "test-model"
        
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={"error": "Invalid API key"})
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        client.session = mock_session
        
        with pytest.raises(ValueError, match="Invalid API key"):
            await client._make_request(messages, model)
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit(self, client):
        """Test rate limiting with retry."""
        messages = [ChatMessage(role="user", content="Test")]
        model = "test-model"
        
        # First response: rate limited
        mock_response_429 = AsyncMock()
        mock_response_429.status = 429
        mock_response_429.json = AsyncMock(return_value={"error": "Rate limited"})
        
        # Second response: success
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Success after retry"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.side_effect = [
            mock_response_429, mock_response_200
        ]
        
        client.session = mock_session
        
        # Should succeed after retry
        with patch('asyncio.sleep'):  # Speed up test
            result = await client._make_request(messages, model)
            assert result["choices"][0]["message"]["content"] == "Success after retry"
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self, client):
        """Test timeout handling."""
        messages = [ChatMessage(role="user", content="Test")]
        model = "test-model"
        
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError("Request timeout")
        
        client.session = mock_session
        
        with patch('asyncio.sleep'):  # Speed up test
            with pytest.raises(asyncio.TimeoutError):
                await client._make_request(messages, model)
    
    def test_parse_response_success(self, client):
        """Test successful response parsing."""
        response_data = {
            "choices": [{"message": {"content": "Parsed content"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }
        
        result = client._parse_response(response_data, "test-model")
        
        assert isinstance(result, AIResponse)
        assert result.content == "Parsed content"
        assert result.model == "test-model"
        assert result.usage["total_tokens"] == 15
        assert result.cost_estimate > 0
    
    def test_parse_response_error(self, client):
        """Test parsing response with error."""
        response_data = {
            "error": {"message": "API error occurred"}
        }
        
        with pytest.raises(ValueError, match="API error: API error occurred"):
            client._parse_response(response_data, "test-model")
    
    def test_parse_response_no_choices(self, client):
        """Test parsing response without choices."""
        response_data = {"choices": []}
        
        with pytest.raises(ValueError, match="No response choices in API response"):
            client._parse_response(response_data, "test-model")


class TestMultiLLMClient:
    """Test MultiLLMClient functionality."""
    
    @pytest.fixture
    def multi_client(self):
        """Create MultiLLMClient."""
        config = Mock(spec=ConfigManager)
        return MultiLLMClient(config)
    
    @pytest.mark.asyncio
    async def test_get_openrouter_client(self, multi_client):
        """Test getting OpenRouter client."""
        client = await multi_client.get_client("openrouter")
        assert isinstance(client, OpenRouterClient)
        
        # Should return same instance on subsequent calls
        client2 = await multi_client.get_client("openrouter")
        assert client is client2
    
    @pytest.mark.asyncio
    async def test_unsupported_provider(self, multi_client):
        """Test unsupported provider error."""
        with pytest.raises(ValueError, match="Unsupported AI provider: unknown"):
            await multi_client.get_client("unknown")
    
    @pytest.mark.asyncio
    async def test_generate_response_via_multi_client(self, multi_client):
        """Test response generation through MultiLLMClient."""
        messages = [ChatMessage(role="user", content="Test")]
        
        mock_response = AIResponse(
            content="Multi-client response",
            model="test-model",
            usage={"total_tokens": 20},
            timestamp=datetime.now()
        )
        
        with patch.object(multi_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await multi_client.generate_response(messages, provider="openrouter")
            
            assert result == mock_response
            mock_client.generate_response.assert_called_once_with(messages)
    
    @pytest.mark.asyncio
    async def test_close_all_sessions(self, multi_client):
        """Test closing all client sessions."""
        # Create a client
        await multi_client.get_client("openrouter")
        
        with patch.object(multi_client.openrouter_client, 'close_session') as mock_close:
            await multi_client.close_all_sessions()
            mock_close.assert_called_once()


@pytest.mark.slow
@pytest.mark.integration
class TestOpenRouterIntegration:
    """Integration tests for OpenRouter client (requires API key)."""
    
    @pytest.fixture
    def integration_client(self):
        """Create client for integration testing."""
        config = Mock(spec=ConfigManager)
        # This would use a real API key in integration tests
        config.get_config.side_effect = lambda key, default=None: {
            'openrouter_api_key': 'test-key-for-integration',
            'fallback_models': ['anthropic/claude-3-sonnet-20240229']
        }.get(key, default)
        return OpenRouterClient(config)
    
    @pytest.mark.skip(reason="Requires real API key")
    @pytest.mark.asyncio
    async def test_real_api_call(self, integration_client):
        """Test real API call (skipped unless API key provided)."""
        messages = [ChatMessage(role="user", content="Say hello in one word.")]
        
        response = await integration_client.generate_response(messages)
        
        assert isinstance(response, AIResponse)
        assert len(response.content) > 0
        assert response.usage["total_tokens"] > 0
        assert response.cost_estimate > 0