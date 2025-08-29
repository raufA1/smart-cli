"""Base Handler for Smart CLI command handlers."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional

from rich.console import Console

console = Console()


class BaseHandler(ABC):
    """Abstract base class for Smart CLI handlers."""

    def __init__(self, smart_cli_instance):
        """Initialize handler with Smart CLI instance reference."""
        self.smart_cli = smart_cli_instance
        self.ai_client = smart_cli_instance.ai_client
        self.ui_manager = None  # UI manager deprecated
        self.config = smart_cli_instance.config
        self.session_manager = smart_cli_instance.session_manager
        self.debug = smart_cli_instance.debug

    @property
    @abstractmethod
    def keywords(self) -> list[str]:
        """Return list of keywords this handler responds to."""
        pass

    @abstractmethod
    async def handle(self, user_input: str) -> bool:
        """Handle user input if it matches this handler's keywords.

        Args:
            user_input: Raw user input string

        Returns:
            bool: True if handled, False if not applicable
        """
        pass

    def matches_input(self, user_input: str) -> bool:
        """Check if user input matches this handler's keywords."""
        lower_input = user_input.lower()
        return any(keyword in lower_input for keyword in self.keywords)

    async def safe_execute(self, func, *args, **kwargs) -> Any:
        """Safely execute async function with error handling."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            if self.debug:
                console.print(
                    f"❌ [red]Handler error in {self.__class__.__name__}: {e}[/red]"
                )
                console.print_exception()
            return None

    def log_debug(self, message: str):
        """Log debug message if debug mode is enabled."""
        if self.debug:
            console.print(
                f"🔧 [dim blue][{self.__class__.__name__}] {message}[/dim blue]"
            )

    def extract_content_after_keyword(self, user_input: str, keyword: str) -> str:
        """Extract content that comes after a specific keyword."""
        lower_input = user_input.lower()
        if keyword in lower_input:
            index = lower_input.find(keyword)
            return user_input[index + len(keyword) :].strip()
        return ""
