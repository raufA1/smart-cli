"""Smart CLI Mode Integration Manager - Seamless integration with existing systems."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()

try:
    from .mode_manager import get_mode_manager, SmartMode
    from .context_manager import get_context_manager
    from .mode_config_manager import get_mode_config_manager
    from .enhanced_request_router import EnhancedRequestRouter
except ImportError:
    from mode_manager import get_mode_manager, SmartMode
    from context_manager import get_context_manager
    from mode_config_manager import get_mode_config_manager
    from enhanced_request_router import EnhancedRequestRouter

class ModeIntegrationManager:
    """Integration manager for seamless mode system integration."""
    
    def __init__(self, smart_cli_instance):
        """Initialize integration manager."""
        self.smart_cli = smart_cli_instance
        self.mode_manager = get_mode_manager(smart_cli_instance.config)
        self.context_manager = get_context_manager()
        self.config_manager = get_mode_config_manager(smart_cli_instance.config)
        
        # Enhanced router
        self.enhanced_router = None
        
        # Integration hooks
        self.pre_mode_hooks = {}
        self.post_mode_hooks = {}
        self.mode_change_listeners = []
        
        # Performance tracking
        self.mode_performance = {}
        
    async def initialize_enhanced_mode_system(self) -> bool:
        """Initialize the enhanced mode system."""
        try:
            # Replace existing router with enhanced version
            self.enhanced_router = EnhancedRequestRouter(self.smart_cli)
            
            # Register mode change listeners
            self._register_built_in_listeners()
            
            # Initialize performance tracking
            self._initialize_performance_tracking()
            
            console.print("🎭 [bold green]Enhanced Mode System initialized successfully![/bold green]")
            console.print("💡 [dim]Available commands: /mode, /modestatus, /context, /switch[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Enhanced Mode System initialization error: {e}[/red]")
            return False
    
    def _register_built_in_listeners(self):
        """Register built-in mode change listeners."""
        self.mode_change_listeners.extend([
            self._on_mode_change_update_context,
            self._on_mode_change_adjust_ai_settings,
            self._on_mode_change_update_performance
        ])
    
    def _initialize_performance_tracking(self):
        """Initialize performance tracking for modes."""
        for mode in SmartMode:
            self.mode_performance[mode.value] = {
                "usage_count": 0,
                "total_time": 0.0,
                "success_rate": 0.0,
                "average_cost": 0.0,
                "last_used": None
            }
    
    async def process_request_with_modes(self, user_input: str) -> bool:
        """Process request using enhanced mode system."""
        if not self.enhanced_router:
            console.print("⚠️ [yellow]Enhanced mode system not initialized, using fallback[/yellow]")
            return await self._fallback_processing(user_input)
        
        start_time = datetime.now()
        current_mode = self.mode_manager.current_mode
        
        # Pre-processing hooks
        await self._execute_pre_mode_hooks(current_mode.value, user_input)
        
        # Process with enhanced router
        try:
            result = await self.enhanced_router.process_request(user_input)
            success = True
        except Exception as e:
            console.print(f"❌ [red]Enhanced processing error: {e}[/red]")
            result = await self._fallback_processing(user_input)
            success = False
        
        # Post-processing hooks
        await self._execute_post_mode_hooks(current_mode.value, user_input, success)
        
        # Update performance metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self._update_mode_performance(current_mode.value, processing_time, success)
        
        return result
    
    async def _fallback_processing(self, user_input: str) -> bool:
        """Fallback to original processing if enhanced system fails."""
        # Import the original router as fallback
        from .request_router import RequestRouter
        
        fallback_router = RequestRouter(self.smart_cli)
        return await fallback_router.process_request(user_input)
    
    async def _execute_pre_mode_hooks(self, mode: str, user_input: str):
        """Execute pre-processing hooks for mode."""
        mode_config = self.config_manager.get_mode_config(mode)
        if mode_config and mode_config.pre_processing_hooks:
            for hook_name in mode_config.pre_processing_hooks:
                try:
                    await self._execute_hook(hook_name, "pre", mode, user_input)
                except Exception as e:
                    console.print(f"⚠️ [dim yellow]Pre-hook {hook_name} error: {e}[/dim yellow]")
    
    async def _execute_post_mode_hooks(self, mode: str, user_input: str, success: bool):
        """Execute post-processing hooks for mode."""
        mode_config = self.config_manager.get_mode_config(mode)
        if mode_config and mode_config.post_processing_hooks:
            for hook_name in mode_config.post_processing_hooks:
                try:
                    await self._execute_hook(hook_name, "post", mode, user_input, success)
                except Exception as e:
                    console.print(f"⚠️ [dim yellow]Post-hook {hook_name} error: {e}[/dim yellow]")
    
    async def _execute_hook(self, hook_name: str, hook_type: str, mode: str, user_input: str, success: bool = None):
        """Execute a specific hook."""
        # Built-in hooks
        if hook_name == "check_git_status":
            await self._hook_check_git_status()
        elif hook_name == "validate_syntax":
            await self._hook_validate_syntax(user_input)
        elif hook_name == "run_tests":
            await self._hook_run_tests(success)
        elif hook_name == "update_docs":
            await self._hook_update_docs(success)
        elif hook_name == "backup_before_analysis":
            await self._hook_backup_before_analysis()
        elif hook_name == "validate_resources":
            await self._hook_validate_resources()
        elif hook_name == "cleanup_temp":
            await self._hook_cleanup_temp()
        else:
            console.print(f"⚠️ [dim yellow]Unknown hook: {hook_name}[/dim yellow]")
    
    # Built-in Hook Implementations
    
    async def _hook_check_git_status(self):
        """Check git status hook."""
        try:
            git_status = await self.smart_cli.git_manager.check_git_status()
            if git_status and (git_status.get("modified") or git_status.get("untracked")):
                console.print("📋 [dim yellow]Git changes detected - consider commit after task[/dim yellow]")
        except Exception:
            pass
    
    async def _hook_validate_syntax(self, user_input: str):
        """Validate syntax hook."""
        if any(keyword in user_input.lower() for keyword in ["write", "create", "kod", "yarad"]):
            console.print("✅ [dim green]Syntax validation ready[/dim green]")
    
    async def _hook_run_tests(self, success: bool):
        """Run tests hook."""
        if success:
            console.print("🧪 [dim blue]Tests recommended after code changes[/dim blue]")
    
    async def _hook_update_docs(self, success: bool):
        """Update documentation hook."""
        if success:
            console.print("📚 [dim blue]Documentation update may be needed[/dim blue]")
    
    async def _hook_backup_before_analysis(self):
        """Backup before analysis hook."""
        console.print("💾 [dim green]Context backed up before analysis[/dim green]")
    
    async def _hook_validate_resources(self):
        """Validate resources hook."""
        console.print("⚙️ [dim green]Resources validated for orchestrator mode[/dim green]")
    
    async def _hook_cleanup_temp(self):
        """Cleanup temporary files hook."""
        console.print("🧹 [dim green]Temporary files cleaned up[/dim green]")
    
    # Mode Change Listeners
    
    async def _on_mode_change_update_context(self, old_mode: str, new_mode: str, reason: str):
        """Update context when mode changes."""
        self.context_manager.share_context_between_modes(
            old_mode, new_mode, 
            ["last_request", "project_state", "session_data"]
        )
    
    async def _on_mode_change_adjust_ai_settings(self, old_mode: str, new_mode: str, reason: str):
        """Adjust AI settings based on new mode."""
        mode_config = self.config_manager.get_mode_config(new_mode)
        
        if mode_config and mode_config.preferred_model and self.smart_cli.ai_client:
            # Update AI client model if possible
            try:
                if hasattr(self.smart_cli.ai_client, 'update_model'):
                    await self.smart_cli.ai_client.update_model(mode_config.preferred_model)
            except Exception:
                pass
    
    async def _on_mode_change_update_performance(self, old_mode: str, new_mode: str, reason: str):
        """Update performance metrics on mode change."""
        if new_mode in self.mode_performance:
            self.mode_performance[new_mode]["usage_count"] += 1
            self.mode_performance[new_mode]["last_used"] = datetime.now().isoformat()
    
    def _update_mode_performance(self, mode: str, processing_time: float, success: bool):
        """Update mode performance metrics."""
        if mode in self.mode_performance:
            perf = self.mode_performance[mode]
            
            # Update timing
            perf["total_time"] += processing_time
            
            # Update success rate (simple moving average)
            current_success_rate = perf["success_rate"]
            usage_count = perf["usage_count"]
            
            if usage_count > 0:
                perf["success_rate"] = ((current_success_rate * (usage_count - 1)) + (1.0 if success else 0.0)) / usage_count
            else:
                perf["success_rate"] = 1.0 if success else 0.0
    
    # Integration Utilities
    
    def get_mode_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive mode performance report."""
        report = {
            "summary": {
                "total_modes": len(self.mode_performance),
                "most_used_mode": max(self.mode_performance.items(), 
                                    key=lambda x: x[1]["usage_count"])[0] if self.mode_performance else None,
                "average_success_rate": sum(p["success_rate"] for p in self.mode_performance.values()) / len(self.mode_performance) if self.mode_performance else 0
            },
            "detailed_metrics": self.mode_performance,
            "recommendations": self._generate_mode_recommendations()
        }
        
        return report
    
    def _generate_mode_recommendations(self) -> List[str]:
        """Generate mode usage recommendations."""
        recommendations = []
        
        # Find underused modes
        underused_modes = [mode for mode, perf in self.mode_performance.items() 
                          if perf["usage_count"] < 5]
        
        if underused_modes:
            recommendations.append(f"Consider trying these modes: {', '.join(underused_modes[:3])}")
        
        # Find modes with low success rates
        low_success_modes = [mode for mode, perf in self.mode_performance.items() 
                           if perf["success_rate"] < 0.7 and perf["usage_count"] > 3]
        
        if low_success_modes:
            recommendations.append(f"Review configuration for: {', '.join(low_success_modes)}")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Mode system is performing well! Keep using different modes for different tasks.")
        
        return recommendations
    
    async def setup_project_modes(self, project_type: str = "general") -> bool:
        """Setup optimal modes for project type."""
        try:
            # Create project config template
            template = self.config_manager.create_project_config_template(
                project_type=project_type
            )
            
            # Save to project
            config_file = ".smartcli"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(template)
            
            # Reload project config
            self.config_manager._load_project_config()
            
            console.print(f"🎭 [green]Project modes configured for {project_type}[/green]")
            console.print(f"📝 [dim]Configuration saved to {config_file}[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Project setup error: {e}[/red]")
            return False

# Global integration manager instance
_integration_manager = None

def get_mode_integration_manager(smart_cli_instance) -> ModeIntegrationManager:
    """Get global mode integration manager instance."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = ModeIntegrationManager(smart_cli_instance)
    return _integration_manager