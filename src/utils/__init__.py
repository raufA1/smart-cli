"""Essential utilities for Smart CLI - minimal, clean architecture."""

from .config import ConfigManager
from .simple_ai_client import AIClient, OpenRouterClient

__all__ = ["OpenRouterClient", "AIClient", "ConfigManager"]
