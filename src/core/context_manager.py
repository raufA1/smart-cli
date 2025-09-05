"""Smart CLI Context Manager - Isolated contexts with intelligent data flow."""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum

from rich.console import Console

console = Console()

class ContextScope(Enum):
    """Context isolation levels."""
    
    MODE_ISOLATED = "mode_isolated"        # Tam ayrı context hər mode üçün
    SHARED_MEMORY = "shared_memory"        # Ortaq yaddaş, ayrı execution
    CROSS_REFERENCE = "cross_reference"    # Mode-lar arası referans
    GLOBAL_STATE = "global_state"          # Ümumi sistem state-i

@dataclass
class ContextData:
    """Context data structure with metadata."""
    
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    scope: ContextScope = ContextScope.MODE_ISOLATED
    
    def update_access(self):
        """Update access metadata."""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1

class SmartContextManager:
    """Advanced context management with intelligent isolation and sharing."""
    
    def __init__(self):
        # Mode-specific isolated contexts
        self.mode_contexts: Dict[str, ContextData] = {}
        
        # Shared memory accessible across modes
        self.shared_memory: ContextData = ContextData(scope=ContextScope.SHARED_MEMORY)
        
        # Cross-reference data between modes
        self.cross_references: Dict[str, Dict[str, Any]] = {}
        
        # Global system state
        self.global_state: ContextData = ContextData(scope=ContextScope.GLOBAL_STATE)
        
        # Context flow rules
        self.context_flow_rules = self._initialize_flow_rules()
        
        # Persistence
        self.context_file = ".smart_context.json"
        self._load_persistent_context()
    
    def _initialize_flow_rules(self) -> Dict[str, Dict[str, List[str]]]:
        """Context flow rules between modes."""
        return {
            # Kod mode-dan architect mode-a nə keçir
            "code_to_architect": {
                "allowed_keys": ["project_structure", "design_patterns", "requirements"],
                "transform_keys": {"implementation_details": "high_level_overview"}
            },
            
            # Analysis mode-dan code mode-a nə keçir
            "analysis_to_code": {
                "allowed_keys": ["issues_found", "optimization_suggestions", "code_quality"],
                "transform_keys": {"detailed_analysis": "action_items"}
            },
            
            # Architect mode-dan bütün mode-lara nə keçir
            "architect_to_all": {
                "allowed_keys": ["system_design", "architecture_decisions", "tech_stack"],
                "auto_share": True
            },
            
            # Learning mode heç nə paylaşmır (read-only)
            "learning_isolation": {
                "allowed_keys": [],
                "read_only": True
            },
            
            # Fast mode minimal context
            "fast_minimal": {
                "allowed_keys": ["quick_commands", "last_directory"],
                "lightweight": True
            }
        }
    
    def _load_persistent_context(self):
        """Load persistent context data."""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Load shared memory
                    if 'shared_memory' in data:
                        self.shared_memory.data = data['shared_memory'].get('data', {})
                        self.shared_memory.metadata = data['shared_memory'].get('metadata', {})
                    
                    # Load global state
                    if 'global_state' in data:
                        self.global_state.data = data['global_state'].get('data', {})
                        self.global_state.metadata = data['global_state'].get('metadata', {})
                    
                    # Load cross-references
                    self.cross_references = data.get('cross_references', {})
                    
        except Exception as e:
            console.print(f"⚠️ [dim yellow]Context load error: {e}[/dim yellow]")
    
    def _save_persistent_context(self):
        """Save persistent context data."""
        try:
            data = {
                'shared_memory': {
                    'data': self.shared_memory.data,
                    'metadata': self.shared_memory.metadata
                },
                'global_state': {
                    'data': self.global_state.data,
                    'metadata': self.global_state.metadata
                },
                'cross_references': self.cross_references,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            console.print(f"⚠️ [dim yellow]Context save error: {e}[/dim yellow]")
    
    def get_mode_context(self, mode: str) -> Dict[str, Any]:
        """Get complete context for a specific mode."""
        # Initialize mode context if not exists
        if mode not in self.mode_contexts:
            self.mode_contexts[mode] = ContextData()
        
        context = self.mode_contexts[mode]
        context.update_access()
        
        # Combine with accessible shared data
        combined_context = {
            # Mode-specific data
            "mode_specific": context.data.copy(),
            
            # Shared memory (read access)
            "shared_memory": self._get_shared_memory_for_mode(mode),
            
            # Cross-references from other modes
            "references": self._get_cross_references_for_mode(mode),
            
            # Global state (filtered)
            "global": self._get_global_state_for_mode(mode),
            
            # Metadata
            "metadata": {
                "mode": mode,
                "last_accessed": context.last_accessed,
                "access_count": context.access_count,
                "context_size": len(str(context.data))
            }
        }
        
        return combined_context
    
    def update_mode_context(self, mode: str, updates: Dict[str, Any], 
                          share_keys: Optional[List[str]] = None):
        """Update mode context with optional sharing."""
        # Initialize if needed
        if mode not in self.mode_contexts:
            self.mode_contexts[mode] = ContextData()
        
        context = self.mode_contexts[mode]
        
        # Update mode-specific data
        context.data.update(updates)
        context.update_access()
        
        # Handle sharing based on rules
        if share_keys:
            self._handle_context_sharing(mode, updates, share_keys)
        
        # Auto-save important changes
        if any(key in updates for key in ["project_structure", "system_design", "critical_error"]):
            self._save_persistent_context()
    
    def _handle_context_sharing(self, source_mode: str, data: Dict[str, Any], 
                              share_keys: List[str]):
        """Handle context sharing based on rules."""
        for key in share_keys:
            if key in data:
                # Add to shared memory
                self.shared_memory.data[f"{source_mode}_{key}"] = {
                    "value": data[key],
                    "source_mode": source_mode,
                    "shared_at": datetime.now().isoformat()
                }
                
                # Create cross-reference
                if source_mode not in self.cross_references:
                    self.cross_references[source_mode] = {}
                self.cross_references[source_mode][key] = {
                    "shared_to": "all",
                    "type": type(data[key]).__name__
                }
    
    def share_context_between_modes(self, from_mode: str, to_mode: str, 
                                   keys: List[str], transform: bool = True):
        """Explicit context sharing between specific modes."""
        if from_mode not in self.mode_contexts:
            return
        
        source_data = self.mode_contexts[from_mode].data
        
        # Get sharing rules
        rule_key = f"{from_mode}_to_{to_mode}"
        rules = self.context_flow_rules.get(rule_key, {})
        
        # Filter allowed keys
        allowed_keys = rules.get("allowed_keys", keys)
        filtered_keys = [k for k in keys if k in allowed_keys or "all" in allowed_keys]
        
        if not filtered_keys:
            console.print(f"⚠️ [yellow]No allowed context keys from {from_mode} to {to_mode}[/yellow]")
            return
        
        # Initialize target mode if needed
        if to_mode not in self.mode_contexts:
            self.mode_contexts[to_mode] = ContextData()
        
        # Transfer data with optional transformation
        shared_data = {}
        transform_rules = rules.get("transform_keys", {})
        
        for key in filtered_keys:
            if key in source_data:
                # Transform key name if needed
                target_key = transform_rules.get(key, key)
                
                # Transform value if needed and transform flag is True
                if transform and key in transform_rules:
                    shared_data[target_key] = self._transform_context_value(
                        source_data[key], from_mode, to_mode
                    )
                else:
                    shared_data[target_key] = source_data[key]
        
        # Update target context
        self.mode_contexts[to_mode].data.update(shared_data)
        self.mode_contexts[to_mode].metadata[f"shared_from_{from_mode}"] = {
            "keys": list(shared_data.keys()),
            "shared_at": datetime.now().isoformat()
        }
        
        console.print(f"✅ [green]Shared {len(shared_data)} context items: {from_mode} → {to_mode}[/green]")
    
    def _transform_context_value(self, value: Any, from_mode: str, to_mode: str) -> Any:
        """Transform context values between modes."""
        # Implementation details → high-level summary
        if from_mode == "code" and to_mode == "architect":
            if isinstance(value, dict) and "implementation" in str(value).lower():
                return {"summary": f"Implementation approach defined", "details_available": True}
        
        # Detailed analysis → action items
        elif from_mode == "analysis" and to_mode == "code":
            if isinstance(value, list):
                return [{"action": item, "priority": "normal"} for item in value[:5]]
        
        # Default: return as-is
        return value
    
    def _get_shared_memory_for_mode(self, mode: str) -> Dict[str, Any]:
        """Get shared memory accessible to specific mode."""
        # Learning mode: read-only access
        if mode == "learning":
            return {k: v["value"] for k, v in self.shared_memory.data.items() 
                   if not k.startswith("sensitive_")}
        
        # Fast mode: minimal context
        elif mode == "fast":
            return {k: v["value"] for k, v in self.shared_memory.data.items() 
                   if k.startswith(("quick_", "last_", "current_"))}
        
        # Other modes: full access
        else:
            return {k: v["value"] if isinstance(v, dict) and "value" in v else v 
                   for k, v in self.shared_memory.data.items()}
    
    def _get_cross_references_for_mode(self, mode: str) -> Dict[str, Any]:
        """Get cross-references available to specific mode."""
        references = {}
        
        for source_mode, refs in self.cross_references.items():
            if source_mode != mode:  # Don't include self-references
                references[source_mode] = refs
        
        return references
    
    def _get_global_state_for_mode(self, mode: str) -> Dict[str, Any]:
        """Get global state accessible to specific mode."""
        # Filter global state based on mode permissions
        sensitive_keys = ["api_keys", "tokens", "passwords"]
        
        filtered_state = {}
        for k, v in self.global_state.data.items():
            if not any(sensitive in k.lower() for sensitive in sensitive_keys):
                filtered_state[k] = v
        
        return filtered_state
    
    def clear_mode_context(self, mode: str, preserve_shared: bool = True):
        """Clear mode-specific context."""
        if mode in self.mode_contexts:
            if preserve_shared:
                # Preserve shared data
                shared_data = {k: v for k, v in self.mode_contexts[mode].data.items() 
                             if k.startswith(("shared_", "global_"))}
                self.mode_contexts[mode] = ContextData()
                self.mode_contexts[mode].data = shared_data
            else:
                del self.mode_contexts[mode]
            
            console.print(f"🗑️ [yellow]Cleared context for {mode} mode[/yellow]")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get comprehensive context summary."""
        return {
            "active_modes": list(self.mode_contexts.keys()),
            "mode_contexts": {
                mode: {
                    "size": len(str(context.data)),
                    "last_accessed": context.last_accessed,
                    "access_count": context.access_count
                }
                for mode, context in self.mode_contexts.items()
            },
            "shared_memory_size": len(self.shared_memory.data),
            "cross_references_count": sum(len(refs) for refs in self.cross_references.values()),
            "global_state_size": len(self.global_state.data)
        }
    
    def optimize_context_memory(self):
        """Optimize context memory usage."""
        # Remove old unused contexts
        cutoff_time = datetime.now().timestamp() - (24 * 3600)  # 24 hours
        
        modes_to_remove = []
        for mode, context in self.mode_contexts.items():
            try:
                last_access = datetime.fromisoformat(context.last_accessed).timestamp()
                if last_access < cutoff_time and context.access_count < 3:
                    modes_to_remove.append(mode)
            except:
                continue
        
        for mode in modes_to_remove:
            self.clear_mode_context(mode)
        
        # Clean up old shared memory
        old_shared_keys = []
        for key, value in self.shared_memory.data.items():
            if isinstance(value, dict) and "shared_at" in value:
                try:
                    shared_time = datetime.fromisoformat(value["shared_at"]).timestamp()
                    if shared_time < cutoff_time:
                        old_shared_keys.append(key)
                except:
                    continue
        
        for key in old_shared_keys:
            del self.shared_memory.data[key]
        
        # Save optimized context
        self._save_persistent_context()
        
        if modes_to_remove or old_shared_keys:
            console.print(f"🧹 [green]Context optimized: removed {len(modes_to_remove)} mode contexts, {len(old_shared_keys)} old shared items[/green]")

# Global context manager instance
_context_manager = None

def get_context_manager() -> SmartContextManager:
    """Get global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = SmartContextManager()
    return _context_manager