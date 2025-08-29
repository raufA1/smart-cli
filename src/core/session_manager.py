"""Smart CLI Session Manager - Core session handling."""

import asyncio
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


class SessionManager:
    """Manages Smart CLI session lifecycle and state."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session_id = f"smart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.conversation_history = []
        self.session_active = False

    def display_welcome(self):
        """Display Smart CLI welcome message."""
        from rich.text import Text

        # Clean startup banner
        console.print("─" * 80, style="dim")

        import os

        current_project = os.path.basename(os.getcwd())

        header = Text()
        header.append("SMART CLI", style="bold cyan")
        header.append(" - Project: ", style="dim")
        header.append(current_project, style="bold white")

        console.print(header)
        console.print("─" * 50, style="dim")

        # System status
        console.print("(✓) Sistem Statusu: ", style="green", end="")
        console.print("Tam Hazır", style="bold green")
        console.print()

        # Ready message
        console.print("Sizə necə kömək edə bilərəm?", style="bold white")

    async def start_session(self):
        """Start interactive session."""
        self.session_active = True
        self.display_welcome()
        return True

    async def end_session(self):
        """End session gracefully."""
        self.session_active = False
        duration = datetime.now() - self.start_time
        console.print(f"\n👋 [yellow]Session ended after {duration}[/yellow]")

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

    def get_recent_history(self, count: int = 10):
        """Get recent conversation history."""
        return self.conversation_history[-count:]
