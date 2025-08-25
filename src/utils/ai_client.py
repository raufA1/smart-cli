"""AI client implementation with OpenRouter API integration."""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import structlog

from .config import ConfigManager


@dataclass
class AIResponse:
    """AI response data class."""
    content: str
    model: str
    usage: Dict[str, int]
    timestamp: datetime
    cost_estimate: Optional[float] = None


@dataclass
class ChatMessage:
    """Chat message data class."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[datetime] = None


class OpenRouterClient:
    """OpenRouter API client with fallback support."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.logger = structlog.get_logger()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API configuration
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = self.config.get_config('openrouter_api_key')
        
        # Fallback models in order of preference
        self.fallback_models = self.config.get_config('fallback_models', [
            "anthropic/claude-3-sonnet-20240229",
            "openai/gpt-4-turbo",
            "google/gemini-pro",
            "meta-llama/llama-2-70b-chat",
        ])
        
        # Rate limiting and retry configuration
        self.max_retries = self.config.get_config('max_retries', 3)
        self.timeout = self.config.get_config('timeout', 30)
        self.retry_delay = 1.0  # Base delay between retries
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.request_count = 0
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self):
        """Start aiohttp session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def generate_response(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate AI response with automatic fallback.
        
        Args:
            messages: List of chat messages
            model: Specific model to use (optional)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum response tokens
            **kwargs: Additional API parameters
            
        Returns:
            AIResponse object with generated content
            
        Raises:
            Exception: If all models fail
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        await self.start_session()
        
        # Use specified model or try fallbacks
        models_to_try = [model] if model else self.fallback_models
        
        for attempt_model in models_to_try:
            if not attempt_model:
                continue
                
            try:
                self.logger.info("Attempting generation", model=attempt_model)
                response = await self._make_request(
                    messages=messages,
                    model=attempt_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Track usage
                self.request_count += 1
                if 'usage' in response:
                    tokens = response['usage'].get('total_tokens', 0)
                    self.total_tokens_used += tokens
                
                # Parse response
                ai_response = self._parse_response(response, attempt_model)
                
                self.logger.info(
                    "Generation successful",
                    model=attempt_model,
                    tokens=ai_response.usage.get('total_tokens', 0)
                )
                
                return ai_response
                
            except Exception as e:
                self.logger.warning(
                    "Model failed, trying next",
                    model=attempt_model,
                    error=str(e)
                )
                
                # If it's the last model, re-raise the exception
                if attempt_model == models_to_try[-1]:
                    raise
                
                # Wait before trying next model
                await asyncio.sleep(self.retry_delay)
                continue
        
        raise Exception("All AI models failed")
    
    async def _make_request(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter API with retries."""
        
        # Prepare request data
        data = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature or self.config.get_config('temperature', 0.7),
            "max_tokens": max_tokens or self.config.get_config('max_tokens', 4000),
        }
        
        # Add additional parameters
        data.update(kwargs)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://smart-cli.dev",  # Required for OpenRouter
            "X-Title": "Smart CLI",  # Optional but recommended
        }
        
        # Retry logic with exponential backoff
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=data,
                    headers=headers
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    
                    # Handle specific HTTP errors
                    elif response.status == 401:
                        raise ValueError("Invalid API key")
                    elif response.status == 429:
                        # Rate limited - wait longer
                        wait_time = self.retry_delay * (2 ** attempt) * 2
                        self.logger.warning(
                            "Rate limited, waiting",
                            wait_time=wait_time,
                            attempt=attempt + 1
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status >= 500:
                        # Server error - retry
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Server error: {response_data.get('error', 'Unknown')}"
                        )
                    else:
                        # Client error - don't retry
                        error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                        raise ValueError(f"API error: {error_msg}")
                        
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                
                self.logger.warning(
                    "Request failed, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    wait_time=wait_time
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise last_exception
        
        raise last_exception or Exception("Max retries exceeded")
    
    def _parse_response(self, response_data: Dict[str, Any], model: str) -> AIResponse:
        """Parse OpenRouter API response."""
        
        if 'error' in response_data:
            raise ValueError(f"API error: {response_data['error'].get('message', 'Unknown')}")
        
        if 'choices' not in response_data or not response_data['choices']:
            raise ValueError("No response choices in API response")
        
        choice = response_data['choices'][0]
        
        if 'message' not in choice:
            raise ValueError("No message in response choice")
        
        content = choice['message'].get('content', '')
        usage = response_data.get('usage', {})
        
        # Estimate cost based on usage
        cost_estimate = self._estimate_cost(usage, model)
        
        return AIResponse(
            content=content,
            model=model,
            usage=usage,
            timestamp=datetime.now(),
            cost_estimate=cost_estimate
        )
    
    def _estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Estimate cost based on token usage and model."""
        
        # Rough cost estimates per 1K tokens (as of 2024)
        # These should be updated based on actual pricing
        cost_per_1k_tokens = {
            "anthropic/claude-3-sonnet-20240229": 0.003,
            "anthropic/claude-3-haiku-20240307": 0.00025,
            "openai/gpt-4-turbo": 0.01,
            "openai/gpt-3.5-turbo": 0.0005,
            "google/gemini-pro": 0.0005,
            "meta-llama/llama-2-70b-chat": 0.0007,
        }
        
        base_cost = cost_per_1k_tokens.get(model, 0.001)  # Default fallback cost
        total_tokens = usage.get('total_tokens', 0)
        
        estimated_cost = (total_tokens / 1000) * base_cost
        self.total_cost += estimated_cost
        
        return estimated_cost
    
    async def stream_response(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ):
        """Stream AI response for real-time output."""
        # For now, implement as regular response
        # TODO: Implement actual streaming
        response = await self.generate_response(messages, model, **kwargs)
        yield response.content
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens_used,
            'estimated_cost': self.total_cost,
            'average_tokens_per_request': (
                self.total_tokens_used / self.request_count
                if self.request_count > 0 else 0
            ),
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.request_count = 0


class MultiLLMClient:
    """Multi-LLM client supporting different providers."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.openrouter_client = None
        self.logger = structlog.get_logger()
    
    async def get_client(self, provider: str = "openrouter") -> OpenRouterClient:
        """Get AI client for specified provider."""
        
        if provider == "openrouter":
            if not self.openrouter_client:
                self.openrouter_client = OpenRouterClient(self.config)
            return self.openrouter_client
        
        # Add support for other providers in the future
        # elif provider == "anthropic":
        #     return AnthropicClient(self.config)
        # elif provider == "openai":
        #     return OpenAIClient(self.config)
        
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    async def generate_response(
        self,
        messages: List[ChatMessage],
        provider: str = "openrouter",
        **kwargs
    ) -> AIResponse:
        """Generate response using specified provider."""
        
        client = await self.get_client(provider)
        return await client.generate_response(messages, **kwargs)
    
    async def close_all_sessions(self):
        """Close all active sessions."""
        if self.openrouter_client:
            await self.openrouter_client.close_session()