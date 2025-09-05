"""Smart CLI Mode Configuration Manager - Advanced mode customization system."""

import json
import os
import yaml
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

from rich.console import Console

console = Console()

@dataclass
class AdvancedModeConfig:
    """Advanced mode configuration with extended features."""
    
    # Basic config
    name: str
    description: str
    preferred_model: Optional[str] = None
    fallback_models: List[str] = field(default_factory=list)
    
    # Tool and permission management
    allowed_tools: Set[str] = field(default_factory=set)
    restricted_tools: Set[str] = field(default_factory=set)
    permissions: Dict[str, bool] = field(default_factory=dict)
    
    # Context and memory settings
    context_size: int = 4000
    max_memory_items: int = 100
    auto_save_context: bool = True
    context_sharing_rules: Dict[str, List[str]] = field(default_factory=dict)
    
    # Behavior settings
    auto_approve: bool = False
    confirmation_required: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    
    # UI and UX settings
    mode_indicator: str = ""
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    display_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced features
    pre_processing_hooks: List[str] = field(default_factory=list)
    post_processing_hooks: List[str] = field(default_factory=list)
    custom_handlers: List[str] = field(default_factory=list)
    
    # Cost and resource management
    cost_limits: Dict[str, float] = field(default_factory=dict)
    resource_limits: Dict[str, int] = field(default_factory=dict)

@dataclass
class ProjectModeConfig:
    """Project-specific mode configuration."""
    
    project_name: str
    project_path: str
    default_mode: str = "smart"
    
    # Project-specific mode overrides
    mode_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Project settings
    project_type: str = "general"  # web, mobile, data, devops, etc.
    tech_stack: List[str] = field(default_factory=list)
    
    # Integration settings
    integrations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Team settings
    team_settings: Dict[str, Any] = field(default_factory=dict)

class SmartModeConfigManager:
    """Advanced configuration manager for Smart CLI modes."""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.project_configs: Dict[str, ProjectModeConfig] = {}
        self.global_config_file = os.path.expanduser("~/.smart_cli_modes.yaml")
        self.project_config_file = ".smartcli"
        
        # Built-in mode templates
        self.mode_templates = self._initialize_mode_templates()
        
        # Load configurations
        self._load_global_config()
        self._load_project_config()
    
    def _initialize_mode_templates(self) -> Dict[str, AdvancedModeConfig]:
        """Initialize built-in mode configuration templates."""
        return {
            "smart": AdvancedModeConfig(
                name="Smart Auto-Detection",
                description="Intelligent request classification and adaptive processing",
                allowed_tools={"all"},
                context_size=4000,
                permissions={"read": True, "write": True, "execute": True},
                mode_indicator="🤖",
                custom_prompts={
                    "welcome": "Smart mode aktiv - intelligent processing",
                    "suggestion": "💡 Mode suggestions available"
                },
                display_settings={
                    "show_classification": True,
                    "show_confidence": True,
                    "suggest_switches": True
                }
            ),
            
            "code": AdvancedModeConfig(
                name="Code Development",
                description="Focused development environment with orchestrator support",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                fallback_models=["anthropic/claude-3-haiku-20240307"],
                allowed_tools={"file_edit", "terminal", "git", "search", "analysis", "test"},
                confirmation_required=["file_delete", "git_reset"],
                context_size=8000,
                max_memory_items=200,
                permissions={"read": True, "write": True, "execute": True},
                mode_indicator="💻",
                custom_prompts={
                    "welcome": "Code mode aktiv - development focused",
                    "pre_task": "Kod taskını analyze edirəm...",
                    "post_task": "Implementation complete ✅"
                },
                pre_processing_hooks=["check_git_status", "validate_syntax"],
                post_processing_hooks=["run_tests", "update_docs"],
                cost_limits={"per_session": 10.0, "per_task": 2.0}
            ),
            
            "analysis": AdvancedModeConfig(
                name="Code Analysis & Review",
                description="Deep code analysis and review with security focus",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                allowed_tools={"file_read", "search", "analysis", "security_scan"},
                restricted_tools={"file_edit", "file_delete"},
                context_size=12000,
                permissions={"read": True, "write": False, "execute": False},
                mode_indicator="🔍",
                custom_prompts={
                    "welcome": "Analysis mode aktiv - read-only deep analysis",
                    "analysis_start": "Detailed analysis başlayır...",
                    "security_check": "🛡️ Security analysis included"
                },
                pre_processing_hooks=["backup_before_analysis"],
                cost_limits={"per_session": 5.0}
            ),
            
            "architect": AdvancedModeConfig(
                name="System Architecture",
                description="High-level system design and architecture planning",
                preferred_model="anthropic/claude-3-opus-20240229",
                allowed_tools={"analysis", "documentation", "search", "diagram"},
                context_size=16000,
                max_memory_items=300,
                permissions={"read": True, "write": True, "execute": False},
                mode_indicator="🏗️",
                custom_prompts={
                    "welcome": "Architecture mode aktiv - system design focus",
                    "design_start": "🏗️ System design analysis başlayır...",
                    "documentation": "📚 Architecture documentation yaradılır"
                },
                context_sharing_rules={
                    "share_to_all": ["system_design", "architecture_decisions", "tech_stack"]
                },
                cost_limits={"per_session": 15.0}
            ),
            
            "learning": AdvancedModeConfig(
                name="Learning Assistant",
                description="Educational explanations and interactive learning",
                preferred_model="anthropic/claude-3-sonnet-20240229",
                allowed_tools={"search", "documentation", "tutorial"},
                restricted_tools={"file_edit", "file_delete", "terminal"},
                context_size=6000,
                permissions={"read": True, "write": False, "execute": False},
                mode_indicator="📚",
                custom_prompts={
                    "welcome": "Learning mode aktiv - educational focus",
                    "explanation_start": "📚 Step-by-step explanation:",
                    "example_provided": "💡 Practical example:"
                },
                display_settings={
                    "show_examples": True,
                    "interactive_mode": True,
                    "progress_tracking": True
                },
                cost_limits={"per_session": 3.0}
            ),
            
            "fast": AdvancedModeConfig(
                name="Fast Operations",
                description="Quick commands and utility operations",
                allowed_tools={"terminal", "git", "file_ops", "quick_search"},
                context_size=2000,
                max_memory_items=50,
                auto_approve=True,
                timeout_seconds=30,
                permissions={"read": True, "write": True, "execute": True},
                mode_indicator="⚡",
                custom_prompts={
                    "welcome": "Fast mode aktiv - quick operations",
                    "quick_task": "⚡ Sürətli icra..."
                },
                display_settings={
                    "minimal_output": True,
                    "show_only_results": True
                },
                cost_limits={"per_task": 0.5}
            ),
            
            "orchestrator": AdvancedModeConfig(
                name="Multi-Agent Orchestrator",
                description="Complex workflows with specialized agent coordination",
                preferred_model="anthropic/claude-3-opus-20240229",
                allowed_tools={"all"},
                context_size=20000,
                max_memory_items=500,
                permissions={"read": True, "write": True, "execute": True},
                mode_indicator="🎭",
                custom_prompts={
                    "welcome": "Orchestrator mode aktiv - multi-agent coordination",
                    "planning": "🎭 Multi-agent plan yaradılır...",
                    "coordination": "🤝 Agent coordination aktiv",
                    "completion": "✅ Multi-agent task tamamlandı"
                },
                context_sharing_rules={
                    "share_between_agents": ["task_results", "intermediate_outputs", "error_logs"]
                },
                pre_processing_hooks=["validate_resources", "check_dependencies"],
                post_processing_hooks=["consolidate_results", "cleanup_temp"],
                cost_limits={"per_session": 25.0, "per_agent": 5.0},
                resource_limits={"max_concurrent_agents": 5, "max_execution_time": 1800}
            )
        }
    
    def _load_global_config(self):
        """Load global mode configuration."""
        try:
            if os.path.exists(self.global_config_file):
                with open(self.global_config_file, 'r', encoding='utf-8') as f:
                    global_config = yaml.safe_load(f)
                    self._apply_global_overrides(global_config)
        except Exception as e:
            if os.path.exists(self.global_config_file):  # Only warn if file exists but can't be loaded
                console.print(f"⚠️ [yellow]Global config load error: {e}[/yellow]")
    
    def _load_project_config(self):
        """Load project-specific mode configuration."""
        config_files = [".smartcli", ".smartcli.yaml", ".smartcli.json"]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        if config_file.endswith('.json'):
                            project_config = json.load(f)
                        else:
                            project_config = yaml.safe_load(f)
                        
                        self._apply_project_config(project_config, os.getcwd())
                        break
                except Exception as e:
                    console.print(f"⚠️ [yellow]Project config error ({config_file}): {e}[/yellow]")
    
    def _apply_global_overrides(self, config: Dict):
        """Apply global configuration overrides."""
        if 'modes' in config:
            for mode_name, mode_overrides in config['modes'].items():
                if mode_name in self.mode_templates:
                    self._update_mode_config(self.mode_templates[mode_name], mode_overrides)
    
    def _apply_project_config(self, config: Dict, project_path: str):
        """Apply project-specific configuration."""
        project_name = config.get('project_name', os.path.basename(project_path))
        
        project_config = ProjectModeConfig(
            project_name=project_name,
            project_path=project_path,
            default_mode=config.get('default_mode', 'smart'),
            project_type=config.get('project_type', 'general'),
            tech_stack=config.get('tech_stack', []),
            integrations=config.get('integrations', {}),
            team_settings=config.get('team_settings', {})
        )
        
        # Apply mode overrides
        if 'modes' in config:
            for mode_name, mode_overrides in config['modes'].items():
                if mode_name in self.mode_templates:
                    # Create a copy of the template for this project
                    project_mode_config = self._copy_mode_config(self.mode_templates[mode_name])
                    self._update_mode_config(project_mode_config, mode_overrides)
                    project_config.mode_overrides[mode_name] = project_mode_config
        
        self.project_configs[project_path] = project_config
    
    def _copy_mode_config(self, config: AdvancedModeConfig) -> AdvancedModeConfig:
        """Create a deep copy of mode configuration."""
        config_dict = asdict(config)
        # Deep copy sets and dicts
        config_dict['allowed_tools'] = set(config_dict['allowed_tools'])
        config_dict['restricted_tools'] = set(config_dict['restricted_tools'])
        return AdvancedModeConfig(**config_dict)
    
    def _update_mode_config(self, config: AdvancedModeConfig, overrides: Dict):
        """Update mode configuration with overrides."""
        for key, value in overrides.items():
            if hasattr(config, key):
                if key in ['allowed_tools', 'restricted_tools'] and isinstance(value, list):
                    setattr(config, key, set(value))
                else:
                    setattr(config, key, value)
    
    def get_mode_config(self, mode_name: str, project_path: str = None) -> Optional[AdvancedModeConfig]:
        """Get mode configuration with project-specific overrides."""
        project_path = project_path or os.getcwd()
        
        # Check for project-specific override
        if project_path in self.project_configs:
            project_config = self.project_configs[project_path]
            if mode_name in project_config.mode_overrides:
                return project_config.mode_overrides[mode_name]
        
        # Return global template
        return self.mode_templates.get(mode_name)
    
    def get_project_config(self, project_path: str = None) -> Optional[ProjectModeConfig]:
        """Get project configuration."""
        project_path = project_path or os.getcwd()
        return self.project_configs.get(project_path)
    
    def create_project_config_template(self, project_path: str = None, project_type: str = "general") -> str:
        """Create a project configuration template."""
        project_path = project_path or os.getcwd()
        project_name = os.path.basename(project_path)
        
        # Tech stack suggestions based on project type
        tech_stacks = {
            "web": ["html", "css", "javascript", "react", "node"],
            "mobile": ["react-native", "flutter", "swift", "kotlin"],
            "data": ["python", "pandas", "jupyter", "sql"],
            "devops": ["docker", "kubernetes", "terraform", "aws"],
            "general": []
        }
        
        template = {
            "project_name": project_name,
            "project_type": project_type,
            "default_mode": "smart",
            "tech_stack": tech_stacks.get(project_type, []),
            
            "modes": {
                "code": {
                    "preferred_model": "anthropic/claude-3-sonnet-20240229",
                    "context_size": 8000,
                    "cost_limits": {"per_session": 10.0}
                },
                "analysis": {
                    "context_size": 12000,
                    "pre_processing_hooks": ["backup_before_analysis"]
                }
            },
            
            "integrations": {
                "github": {"enabled": False},
                "cost_tracking": {"enabled": True, "budget_limit": 50.0}
            },
            
            "team_settings": {
                "shared_modes": ["architect", "learning"],
                "approval_required": ["orchestrator"]
            }
        }
        
        return yaml.dump(template, default_flow_style=False, allow_unicode=True, indent=2)
    
    def save_project_config(self, config: ProjectModeConfig, file_format: str = "yaml"):
        """Save project configuration to file."""
        config_dict = asdict(config)
        
        if file_format == "json":
            config_file = os.path.join(config.project_path, ".smartcli.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        else:
            config_file = os.path.join(config.project_path, ".smartcli.yaml")
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        console.print(f"✅ [green]Project configuration saved: {config_file}[/green]")
    
    def validate_mode_config(self, config: AdvancedModeConfig) -> List[str]:
        """Validate mode configuration and return issues."""
        issues = []
        
        # Check required fields
        if not config.name:
            issues.append("Mode name is required")
        
        if not config.description:
            issues.append("Mode description is required")
        
        # Check tool conflicts
        conflicting_tools = config.allowed_tools.intersection(config.restricted_tools)
        if conflicting_tools:
            issues.append(f"Tools cannot be both allowed and restricted: {conflicting_tools}")
        
        # Check context size limits
        if config.context_size < 1000:
            issues.append("Context size should be at least 1000 tokens")
        elif config.context_size > 100000:
            issues.append("Context size should not exceed 100000 tokens")
        
        # Check cost limits
        for limit_type, limit_value in config.cost_limits.items():
            if limit_value < 0:
                issues.append(f"Cost limit {limit_type} cannot be negative")
        
        return issues
    
    def get_available_modes(self, project_path: str = None) -> List[str]:
        """Get list of available modes for project."""
        modes = list(self.mode_templates.keys())
        
        project_path = project_path or os.getcwd()
        if project_path in self.project_configs:
            project_config = self.project_configs[project_path]
            modes.extend(project_config.mode_overrides.keys())
        
        return sorted(list(set(modes)))
    
    def get_mode_suggestions(self, context: Dict) -> List[str]:
        """Get mode suggestions based on context."""
        suggestions = []
        
        # Analyze context for mode recommendations
        if context.get("has_code_files"):
            suggestions.append("code")
        
        if context.get("is_git_repo"):
            suggestions.append("fast")  # For quick git operations
        
        # Check for analysis keywords
        if any(word in context.get("last_input", "").lower() 
               for word in ["analyze", "review", "check"]):
            suggestions.append("analysis")
        
        # Check for learning keywords
        if any(word in context.get("last_input", "").lower() 
               for word in ["explain", "how", "what", "learn"]):
            suggestions.append("learning")
        
        return suggestions[:3]  # Limit to top 3 suggestions

# Global config manager instance
_mode_config_manager = None

def get_mode_config_manager(config_manager=None) -> SmartModeConfigManager:
    """Get global mode configuration manager instance."""
    global _mode_config_manager
    if _mode_config_manager is None:
        _mode_config_manager = SmartModeConfigManager(config_manager)
    return _mode_config_manager