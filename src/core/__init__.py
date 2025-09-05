"""Smart CLI Core Package - Enhanced with Mode System."""

# Original core modules
from .command_handler import CommandHandler
from .file_manager import FileManager
from .session_manager import SessionManager

# Enhanced mode system modules
try:
    from .mode_manager import SmartModeManager, SmartMode, get_mode_manager
    from .context_manager import SmartContextManager, get_context_manager
    from .enhanced_request_router import EnhancedRequestRouter
    from .mode_config_manager import SmartModeConfigManager, get_mode_config_manager
    from .mode_integration_manager import ModeIntegrationManager, get_mode_integration_manager
    from .mode_system_activator import ModeSystemActivator, get_mode_system_activator
    
    MODE_SYSTEM_AVAILABLE = True
except ImportError as e:
    MODE_SYSTEM_AVAILABLE = False
    import warnings
    warnings.warn(f"Enhanced Mode System not fully available: {e}", ImportWarning)

# Original modules
try:
    from .request_router import RequestRouter
    from .intelligent_request_classifier import get_intelligent_classifier, RequestType
except ImportError:
    pass

__all__ = [
    "SessionManager", 
    "FileManager", 
    "CommandHandler"
]

# Add mode system components if available
if MODE_SYSTEM_AVAILABLE:
    __all__.extend([
        'SmartModeManager',
        'SmartMode', 
        'get_mode_manager',
        'SmartContextManager',
        'get_context_manager',
        'EnhancedRequestRouter',
        'SmartModeConfigManager',
        'get_mode_config_manager',
        'ModeIntegrationManager',
        'get_mode_integration_manager',
        'ModeSystemActivator',
        'get_mode_system_activator'
    ])