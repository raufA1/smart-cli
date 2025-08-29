"""Enhanced error handling for Smart CLI."""

import logging
import traceback
from typing import Any, Optional, Dict, List
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import json


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    CONFIG = "configuration"
    API = "api_error"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class SmartError:
    """Structured error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    suggestion: Optional[str] = None
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    traceback_info: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
            "error_code": self.error_code,
            "context": self.context,
            "traceback": self.traceback_info
        }


class SmartErrorHandler:
    """Enhanced error handler for Smart CLI."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger("smart_cli_errors")
        self.error_log = []
        
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.WARNING)
    
    def handle_error(
        self, 
        exception: Exception, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None
    ) -> SmartError:
        """Handle and categorize an exception."""
        
        # Determine severity and category
        severity, refined_category = self._classify_error(exception, category)
        
        # Generate user-friendly message and suggestion
        message, suggestion = self._generate_message_and_suggestion(
            exception, refined_category
        )
        
        # Create structured error
        error = SmartError(
            category=refined_category,
            severity=severity,
            message=message,
            details=str(exception),
            suggestion=suggestion,
            error_code=self._generate_error_code(refined_category, exception),
            context=context,
            traceback_info=traceback.format_exc()
        )
        
        # Log the error
        self._log_error(error)
        
        # Store in error history
        self.error_log.append(error)
        
        return error
    
    def _classify_error(
        self, 
        exception: Exception, 
        suggested_category: ErrorCategory
    ) -> tuple[ErrorSeverity, ErrorCategory]:
        """Classify error by type and severity."""
        
        # Map exception types to categories and severities
        exception_mappings = {
            # Configuration errors
            FileNotFoundError: (ErrorSeverity.MEDIUM, ErrorCategory.CONFIG),
            KeyError: (ErrorSeverity.MEDIUM, ErrorCategory.CONFIG),
            ValueError: (ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION),
            
            # API errors
            ConnectionError: (ErrorSeverity.HIGH, ErrorCategory.NETWORK),
            TimeoutError: (ErrorSeverity.MEDIUM, ErrorCategory.TIMEOUT),
            
            # Permission errors
            PermissionError: (ErrorSeverity.HIGH, ErrorCategory.PERMISSION),
            
            # File system errors
            OSError: (ErrorSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM),
            IOError: (ErrorSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM),
        }
        
        exception_type = type(exception)
        
        # Check for specific exception types
        if exception_type in exception_mappings:
            return exception_mappings[exception_type]
        
        # Check for API-related errors by message content
        error_msg = str(exception).lower()
        if any(term in error_msg for term in ["api", "token", "key", "auth"]):
            return ErrorSeverity.HIGH, ErrorCategory.API
        
        if any(term in error_msg for term in ["network", "connection", "request"]):
            return ErrorSeverity.MEDIUM, ErrorCategory.NETWORK
        
        # Use suggested category with default severity
        severity_map = {
            ErrorCategory.CRITICAL: ErrorSeverity.CRITICAL,
            ErrorCategory.API: ErrorSeverity.HIGH,
            ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
            ErrorCategory.PERMISSION: ErrorSeverity.HIGH,
            ErrorCategory.CONFIG: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.FILE_SYSTEM: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.LOW
        }
        
        return severity_map.get(suggested_category, ErrorSeverity.MEDIUM), suggested_category
    
    def _generate_message_and_suggestion(
        self, 
        exception: Exception, 
        category: ErrorCategory
    ) -> tuple[str, str]:
        """Generate user-friendly message and suggestion."""
        
        error_msg = str(exception)
        
        messages_and_suggestions = {
            ErrorCategory.CONFIG: (
                "Configuration issue detected",
                "Check your configuration settings in ~/.smart-cli/ or run '/config show'"
            ),
            ErrorCategory.API: (
                "API connection failed",
                "Verify your API keys are correct and you have internet connectivity"
            ),
            ErrorCategory.NETWORK: (
                "Network connectivity issue",
                "Check your internet connection and try again"
            ),
            ErrorCategory.AUTHENTICATION: (
                "Authentication failed",
                "Verify your API keys and tokens are valid and not expired"
            ),
            ErrorCategory.PERMISSION: (
                "Permission denied",
                "Check file permissions or run with appropriate privileges"
            ),
            ErrorCategory.FILE_SYSTEM: (
                "File system operation failed",
                "Check if the file/directory exists and you have proper permissions"
            ),
            ErrorCategory.VALIDATION: (
                "Input validation failed",
                "Please check your input parameters and try again"
            ),
            ErrorCategory.TIMEOUT: (
                "Operation timed out",
                "Try again or check your network connection"
            ),
            ErrorCategory.UNKNOWN: (
                "An unexpected error occurred",
                "Please check the error details and try again"
            )
        }
        
        base_message, suggestion = messages_and_suggestions.get(
            category, 
            ("An error occurred", "Please try again or contact support")
        )
        
        # Enhance message with specific details for certain errors
        if isinstance(exception, FileNotFoundError):
            if "config" in error_msg.lower():
                base_message = "Configuration file not found"
                suggestion = "Run 'smart setup' to create initial configuration"
            else:
                base_message = f"File not found: {exception.filename}"
        
        elif isinstance(exception, PermissionError):
            base_message = f"Permission denied: {exception.filename}"
            suggestion = "Check file permissions or run as administrator/root"
        
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            base_message = "Invalid or missing API key"
            suggestion = "Set your API key using '/config api-key <your-key>'"
        
        return base_message, suggestion
    
    def _generate_error_code(self, category: ErrorCategory, exception: Exception) -> str:
        """Generate unique error code."""
        category_codes = {
            ErrorCategory.CONFIG: "CFG",
            ErrorCategory.API: "API",
            ErrorCategory.NETWORK: "NET",
            ErrorCategory.AUTHENTICATION: "AUTH",
            ErrorCategory.PERMISSION: "PERM",
            ErrorCategory.FILE_SYSTEM: "FS",
            ErrorCategory.VALIDATION: "VAL",
            ErrorCategory.TIMEOUT: "TMO",
            ErrorCategory.UNKNOWN: "UNK"
        }
        
        category_code = category_codes.get(category, "UNK")
        exception_hash = abs(hash(str(exception))) % 1000
        
        return f"SMART_{category_code}_{exception_hash:03d}"
    
    def _log_error(self, error: SmartError):
        """Log error with appropriate level."""
        severity_to_log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        
        log_level = severity_to_log_level.get(error.severity, logging.ERROR)
        
        log_message = f"[{error.error_code}] {error.message}"
        if error.details:
            log_message += f" - {error.details}"
        
        self.logger.log(log_level, log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.error_log:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }
        
        # Count by category
        by_category = {}
        for error in self.error_log:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in self.error_log:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Get recent errors (last 5)
        recent_errors = [
            {
                "code": error.error_code,
                "message": error.message,
                "category": error.category.value,
                "severity": error.severity.value
            }
            for error in self.error_log[-5:]
        ]
        
        return {
            "total_errors": len(self.error_log),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": recent_errors
        }
    
    def save_error_log(self, file_path: str):
        """Save error log to file."""
        error_data = [error.to_dict() for error in self.error_log]
        
        with open(file_path, 'w') as f:
            json.dump({
                "timestamp": str(Path(__file__).stat().st_mtime),
                "errors": error_data
            }, f, indent=2)
    
    def clear_error_log(self):
        """Clear error history."""
        self.error_log.clear()


# Global error handler instance
_global_error_handler = None


def get_error_handler(log_file: Optional[str] = None) -> SmartErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = SmartErrorHandler(log_file)
    
    return _global_error_handler


def handle_error(
    exception: Exception,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[Dict[str, Any]] = None
) -> SmartError:
    """Convenience function to handle errors."""
    handler = get_error_handler()
    return handler.handle_error(exception, category, context)


def safe_execute(func, *args, **kwargs):
    """Execute function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error = handle_error(e, context={"function": func.__name__})
        return None, error


async def safe_execute_async(func, *args, **kwargs):
    """Execute async function with error handling."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error = handle_error(e, context={"function": func.__name__})
        return None, error