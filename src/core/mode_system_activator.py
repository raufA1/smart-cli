"""Smart CLI Mode System Activator - Seamless integration with existing architecture."""

import asyncio
from typing import Optional

from rich.console import Console

console = Console()

class ModeSystemActivator:
    """Activator for seamless mode system integration."""
    
    def __init__(self, smart_cli_instance):
        """Initialize with Smart CLI instance."""
        self.smart_cli = smart_cli_instance
        self.mode_integration_manager = None
        self.is_activated = False
        
    async def activate_enhanced_mode_system(self) -> bool:
        """Activate the enhanced mode system."""
        try:
            # Import mode integration manager
            from .mode_integration_manager import get_mode_integration_manager
            
            # Initialize integration manager
            self.mode_integration_manager = get_mode_integration_manager(self.smart_cli)
            
            # Initialize enhanced mode system
            success = await self.mode_integration_manager.initialize_enhanced_mode_system()
            
            if success:
                self.is_activated = True
                console.print("🎭 [bold green]Enhanced Mode System activated![/bold green]")
                
                # Show quick help
                self._show_mode_quick_help()
                
                return True
            else:
                console.print("❌ [red]Failed to activate Enhanced Mode System[/red]")
                return False
                
        except Exception as e:
            console.print(f"❌ [red]Mode system activation error: {e}[/red]")
            return False
    
    def _show_mode_quick_help(self):
        """Show quick mode system help."""
        console.print("💡 [dim blue]Quick commands: /mode, /modestatus, /context, /switch[/dim blue]")
        console.print("🎯 [dim]Current mode: smart (auto-detection)[/dim]")
    
    async def process_request_with_modes(self, user_input: str) -> bool:
        """Process request using enhanced mode system if activated."""
        if self.is_activated and self.mode_integration_manager:
            return await self.mode_integration_manager.process_request_with_modes(user_input)
        else:
            # Fallback to original processing
            return await self._fallback_to_original_router(user_input)
    
    async def _fallback_to_original_router(self, user_input: str) -> bool:
        """Fallback to original request router."""
        try:
            from .request_router import RequestRouter
            
            original_router = RequestRouter(self.smart_cli)
            return await original_router.process_request(user_input)
            
        except Exception as e:
            console.print(f"❌ [red]Fallback processing error: {e}[/red]")
            return True
    
    def get_performance_report(self) -> Optional[dict]:
        """Get mode system performance report."""
        if self.is_activated and self.mode_integration_manager:
            return self.mode_integration_manager.get_mode_performance_report()
        return None

# Global activator instance
_mode_activator = None

def get_mode_system_activator(smart_cli_instance) -> ModeSystemActivator:
    """Get global mode system activator."""
    global _mode_activator
    if _mode_activator is None:
        _mode_activator = ModeSystemActivator(smart_cli_instance)
    return _mode_activator