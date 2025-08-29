"""Smart CLI Session Manager - Core session handling."""

import asyncio
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel

try:
    from .budget_profiles import get_profile_manager, UsageProfile
except ImportError:
    from budget_profiles import get_profile_manager, UsageProfile

console = Console()


class SessionManager:
    """Manages Smart CLI session lifecycle and state."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session_id = f"smart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.conversation_history = []
        self.session_active = False
        self.budget_manager = get_profile_manager()
        self.current_profile = None

    def display_welcome(self):
        """Display Smart CLI welcome message."""
        from rich.text import Text

        # Clean startup banner
        console.print("─" * 80, style="dim")

        import os

        try:
            current_project = os.path.basename(os.getcwd())
        except (FileNotFoundError, OSError):
            current_project = "unknown"

        header = Text()
        header.append("SMART CLI", style="bold cyan")
        header.append(" - Project: ", style="dim")
        header.append(current_project, style="bold white")

        console.print(header)
        console.print("─" * 50, style="dim")

        # System status
        console.print("(✓) Sistem Statusu: ", style="green", end="")
        console.print("Tam Hazır", style="bold green")
        
        # Budget profile info
        if self.current_profile:
            profile = self.budget_manager.get_profile(self.current_profile)
            console.print(f"(💰) Budget Profili: {profile.name}", style="cyan")
            console.print(f"    Günlük limit: ${profile.daily_limit:.2f} | Aylıq: ${profile.monthly_limit:.2f}", style="dim cyan")
        else:
            console.print("(💰) Budget Profili: Seçilməyib - 'budget' əmrini istifadə edin", style="dim yellow")
        
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
    
    def set_budget_profile(self, profile_type: UsageProfile):
        """Set current budget profile."""
        self.current_profile = profile_type
        profile = self.budget_manager.get_profile(profile_type)
        console.print(f"✅ Budget profili dəyişdirildi: {profile.name}", style="green")
        console.print(f"   Günlük limit: ${profile.daily_limit:.2f}", style="dim green")
        console.print(f"   Aylıq limit: ${profile.monthly_limit:.2f}", style="dim green")
    
    def get_budget_profile(self):
        """Get current budget profile."""
        return self.current_profile
    
    def show_budget_info(self):
        """Display budget profile information."""
        if not self.current_profile:
            console.print("❌ Budget profili seçilməyib", style="red")
            console.print("Mövcud profillər:", style="bold")
            for profile_type, profile in self.budget_manager.list_profiles().items():
                console.print(f"  • {profile.name}: {profile.description}", style="dim")
                console.print(f"    Günlük: ${profile.daily_limit:.2f}, Aylıq: ${profile.monthly_limit:.2f}", style="dim cyan")
            return
        
        profile = self.budget_manager.get_profile(self.current_profile)
        console.print(f"📊 Cari Budget Profili: {profile.name}", style="bold cyan")
        console.print(f"   {profile.description}", style="dim")
        console.print(f"   Günlük limit: ${profile.daily_limit:.2f}", style="cyan")
        console.print(f"   Aylıq limit: ${profile.monthly_limit:.2f}", style="cyan")
        console.print(f"   Sorğu başına limit: ${profile.per_request_limit:.2f}", style="cyan")
        console.print(f"   Fövqəladə ehtiyat: ${profile.emergency_reserve:.2f}", style="cyan")
