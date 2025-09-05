"""Smart CLI Mode Manager - Intelligent mode switching and context management."""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

console = Console()

class SmartMode(Enum):
    """Smart CLI operational modes."""
    
    SMART = "smart"           # Auto-detection (default)
    CODE = "code"             # Pure development focus
    ANALYSIS = "analysis"     # Code review, debugging, investigation
    ARCHITECT = "architect"   # High-level design, planning
    LEARNING = "learning"     # Educational, explanations
    FAST = "fast"            # Quick commands, utilities
    ORCHESTRATOR = "orchestrator"  # Complex multi-agent workflows

@dataclass
class ModeConfig:
    """Configuration for a specific mode."""
    
    name: str
    description: str
    preferred_model: Optional[str] = None
    allowed_tools: Set[str] = field(default_factory=set)
    context_size: int = 4000
    auto_approve: bool = False
    permissions: Dict[str, bool] = field(default_factory=dict)
    
class ModeMemory:
    """Memory system for mode-specific learning."""
    
    def __init__(self):
        self.mode_memories: Dict[str, Dict[str, Any]] = {}
        self.cross_mode_learnings: Dict[str, Any] = {}
        self.memory_file = ".smart_cli_memory.json"
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.mode_memories = data.get('mode_memories', {})
                    self.cross_mode_learnings = data.get('cross_mode_learnings', {})
        except Exception:
            pass
    
    def _save_memory(self):
        """Save memory to file."""
        try:
            data = {
                'mode_memories': self.mode_memories,
                'cross_mode_learnings': self.cross_mode_learnings,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    async def remember_for_mode(self, mode: str, key: str, value: Any):
        """Store memory for specific mode."""
        if mode not in self.mode_memories:
            self.mode_memories[mode] = {}
        
        self.mode_memories[mode][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'access_count': self.mode_memories[mode].get(key, {}).get('access_count', 0) + 1
        }
        self._save_memory()
    
    async def recall_for_mode(self, mode: str, key: str) -> Optional[Any]:
        """Retrieve memory for specific mode."""
        if mode in self.mode_memories and key in self.mode_memories[mode]:
            memory = self.mode_memories[mode][key]
            memory['access_count'] = memory.get('access_count', 0) + 1
            self._save_memory()
            return memory['value']
        return None
    
    async def suggest_based_on_memory(self, mode: str, context: Dict) -> List[str]:
        """Suggest actions based on mode memory."""
        suggestions = []
        
        if mode in self.mode_memories:
            # Find frequently accessed patterns
            mode_mem = self.mode_memories[mode]
            frequent_items = sorted(
                mode_mem.items(), 
                key=lambda x: x[1].get('access_count', 0), 
                reverse=True
            )[:3]
            
            for key, data in frequent_items:
                if data.get('access_count', 0) > 2:
                    suggestions.append(f"Consider: {key}")
        
        return suggestions

class SmartModeManager:
    """Advanced mode management with intelligent switching and context isolation."""
    
    def __init__(self, config_manager=None):
        self.current_mode = SmartMode.SMART
        self.previous_mode: Optional[SmartMode] = None
        self.mode_history: List[tuple] = []
        self.config_manager = config_manager
        self.memory = ModeMemory()
        
        # Initialize mode configurations
        self.mode_configs = self._initialize_default_configs()
        self._load_project_config()
    
    def _initialize_default_configs(self) -> Dict[SmartMode, ModeConfig]:
        """Initialize default configurations for all modes."""
        return {
            SmartMode.SMART: ModeConfig(
                name="Smart Auto-Detection",
                description="Intelligent request classification and routing",
                allowed_tools={"all"},
                context_size=4000,
                permissions={"read": True, "write": True, "execute": True}
            ),
            SmartMode.CODE: ModeConfig(
                name="Code Development",
                description="Pure development focus with code generation and modification",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                allowed_tools={"file_edit", "terminal", "git", "search", "analysis"},
                context_size=8000,
                permissions={"read": True, "write": True, "execute": True}
            ),
            SmartMode.ANALYSIS: ModeConfig(
                name="Code Analysis",
                description="Code review, debugging, and investigation",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                allowed_tools={"file_read", "search", "analysis", "terminal"},
                context_size=12000,
                permissions={"read": True, "write": False, "execute": False}
            ),
            SmartMode.ARCHITECT: ModeConfig(
                name="System Architect",
                description="High-level design, planning, and architecture",
                preferred_model="anthropic/claude-3-opus-20240229",
                allowed_tools={"analysis", "documentation", "search"},
                context_size=16000,
                permissions={"read": True, "write": True, "execute": False}
            ),
            SmartMode.LEARNING: ModeConfig(
                name="Learning Assistant",
                description="Educational explanations and tutorials",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                allowed_tools={"search", "documentation"},
                context_size=6000,
                permissions={"read": True, "write": False, "execute": False}
            ),
            SmartMode.FAST: ModeConfig(
                name="Quick Commands",
                description="Fast utility operations and simple tasks",
                allowed_tools={"terminal", "git", "file_ops"},
                context_size=2000,
                auto_approve=True,
                permissions={"read": True, "write": True, "execute": True}
            ),
            SmartMode.ORCHESTRATOR: ModeConfig(
                name="Multi-Agent Orchestrator",
                description="Complex workflows with multiple specialized agents",
                preferred_model="anthropic/claude-3-opus-20240229",
                allowed_tools={"all"},
                context_size=20000,
                permissions={"read": True, "write": True, "execute": True}
            )
        }
    
    def _load_project_config(self):
        """Load project-specific mode configuration."""
        config_file = ".smartcli"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    import yaml
                    project_config = yaml.safe_load(f)
                    self._apply_project_config(project_config)
            except Exception as e:
                console.print(f"⚠️ [yellow]Project config error: {e}[/yellow]")
    
    def _apply_project_config(self, config: Dict):
        """Apply project-specific configuration to modes."""
        if 'modes' in config:
            for mode_name, mode_data in config['modes'].items():
                try:
                    mode_enum = SmartMode(mode_name)
                    if mode_enum in self.mode_configs:
                        # Update existing config
                        mode_config = self.mode_configs[mode_enum]
                        if 'preferred_model' in mode_data:
                            mode_config.preferred_model = mode_data['preferred_model']
                        if 'context_size' in mode_data:
                            mode_config.context_size = mode_data['context_size']
                        if 'tools' in mode_data:
                            mode_config.allowed_tools = set(mode_data['tools'])
                except ValueError:
                    continue
    
    async def switch_mode(self, target_mode: str, reason: str = "") -> bool:
        """Switch to target mode with validation."""
        try:
            new_mode = SmartMode(target_mode.lower())
        except ValueError:
            console.print(f"❌ [red]Unknown mode: {target_mode}[/red]")
            return False
        
        if new_mode == self.current_mode:
            console.print(f"ℹ️ Already in {new_mode.value} mode")
            return True
        
        # Store previous mode
        self.previous_mode = self.current_mode
        
        # Add to history
        self.mode_history.append((
            datetime.now().isoformat(),
            self.current_mode.value,
            new_mode.value,
            reason
        ))
        
        # Switch mode
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        # Remember the switch
        await self.memory.remember_for_mode(
            new_mode.value, 
            f"switched_from_{old_mode.value}", 
            {"reason": reason, "timestamp": datetime.now().isoformat()}
        )
        
        console.print(f"🔄 [green]Switched from {old_mode.value} → {new_mode.value} mode[/green]")
        if reason:
            console.print(f"💭 [dim]Reason: {reason}[/dim]")
        
        return True
    
    async def suggest_mode_switch(self, user_input: str, context: Dict) -> Optional[str]:
        """Suggest optimal mode based on input and context."""
        # Analyze input for mode indicators
        input_lower = user_input.lower()
        
        # Development indicators
        dev_patterns = ["create", "build", "implement", "code", "yarad", "yarat", "kodla"]
        if any(pattern in input_lower for pattern in dev_patterns):
            if self.current_mode != SmartMode.CODE:
                return "code"
        
        # Analysis indicators
        analysis_patterns = ["analyze", "review", "check", "debug", "təhlil", "yoxla", "bax"]
        if any(pattern in input_lower for pattern in analysis_patterns):
            if self.current_mode != SmartMode.ANALYSIS:
                return "analysis"
        
        # Architecture indicators
        arch_patterns = ["design", "architecture", "plan", "structure", "dizayn", "quruluş"]
        if any(pattern in input_lower for pattern in arch_patterns):
            if self.current_mode != SmartMode.ARCHITECT:
                return "architect"
        
        # Learning indicators
        learn_patterns = ["explain", "how", "what", "learn", "izah", "necə", "nədir", "öyrət"]
        if any(pattern in input_lower for pattern in learn_patterns):
            if self.current_mode != SmartMode.LEARNING:
                return "learning"
        
        # Quick command indicators
        quick_patterns = ["git", "ls", "cd", "npm", "pip", "quick", "fast"]
        if any(pattern in input_lower for pattern in quick_patterns):
            if self.current_mode != SmartMode.FAST:
                return "fast"
        
        return None
    
    def get_current_config(self) -> ModeConfig:
        """Get current mode configuration."""
        return self.mode_configs[self.current_mode]
    
    def get_mode_permissions(self, mode: SmartMode = None) -> Dict[str, bool]:
        """Get permissions for specified mode (or current)."""
        target_mode = mode or self.current_mode
        return self.mode_configs[target_mode].permissions.copy()
    
    def has_permission(self, action: str) -> bool:
        """Check if current mode has permission for action."""
        permissions = self.get_mode_permissions()
        return permissions.get(action, False)
    
    async def get_mode_suggestions(self, context: Dict) -> List[str]:
        """Get suggestions based on current mode and memory."""
        current_config = self.get_current_config()
        suggestions = []
        
        # Add mode-specific suggestions
        suggestions.append(f"Current: {current_config.name}")
        suggestions.append(f"Tools: {', '.join(list(current_config.allowed_tools)[:3])}")
        
        # Add memory-based suggestions
        memory_suggestions = await self.memory.suggest_based_on_memory(
            self.current_mode.value, context
        )
        suggestions.extend(memory_suggestions)
        
        return suggestions
    
    def get_mode_status(self) -> Dict[str, Any]:
        """Get comprehensive mode status."""
        current_config = self.get_current_config()
        
        return {
            "current_mode": self.current_mode.value,
            "previous_mode": self.previous_mode.value if self.previous_mode else None,
            "description": current_config.description,
            "preferred_model": current_config.preferred_model,
            "context_size": current_config.context_size,
            "permissions": current_config.permissions,
            "tools_count": len(current_config.allowed_tools),
            "history_count": len(self.mode_history),
            "auto_approve": current_config.auto_approve
        }
    
    async def auto_switch_if_beneficial(self, user_input: str, context: Dict) -> bool:
        """Auto-switch mode if it would be beneficial."""
        if self.current_mode != SmartMode.SMART:
            return False  # Only auto-switch from smart mode
        
        suggestion = await self.suggest_mode_switch(user_input, context)
        if suggestion:
            # Auto-switch with low confidence threshold
            await self.switch_mode(suggestion, f"Auto-switched based on input pattern")
            return True
        
        return False

# Global mode manager instance
_mode_manager = None

def get_mode_manager(config_manager=None) -> SmartModeManager:
    """Get global mode manager instance."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = SmartModeManager(config_manager)
    return _mode_manager