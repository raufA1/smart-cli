"""Configuration management for Smart CLI."""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Manual .env file loading
def load_env_file_manual():
    """Load environment variables from .env file manually."""
    # Try current directory first, then parent directories
    try:
        current_dir = Path.cwd()
    except (FileNotFoundError, OSError):
        # Fallback to home directory if current working directory doesn't exist
        current_dir = Path.home()
    
    paths_to_try = [
        current_dir / ".env",
        current_dir.parent / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]

    for env_path in paths_to_try:
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            # Only set if not already in environment (preserve existing values)
                            if key.strip() not in os.environ:
                                os.environ[key.strip()] = value.strip()
                return True
            except Exception as e:
                print(f"Warning: Could not load .env file {env_path}: {e}")
    return False


# Load .env file at module import
load_env_file_manual()


class ConfigManager:
    """Manages Smart CLI configuration with secure storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".smart-cli"
        self.config_file = self.config_dir / "config.yaml"
        self.secure_config_file = self.config_dir / "secure_config.enc"

        # Ensure config directory exists
        try:
            self.config_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError) as e:
            # Log warning but continue with default config
            print(f"Warning: Could not create config directory: {e}")

        # Initialize encryption
        self._init_encryption()

        # Load configuration
        self.config = self._load_config()

    def _init_encryption(self):
        """Initialize encryption for sensitive configuration data."""
        key_file = self.config_dir / "config.key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new encryption key
            password = os.environ.get("SMART_CLI_MASTER_KEY", "default-key-change-me")
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Store key securely
            with open(key_file, "wb") as f:
                f.write(key)

            # Set restrictive permissions
            os.chmod(key_file, 0o600)

        self.cipher = Fernet(key)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from files."""
        config = {}

        # Load general configuration
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config.update(yaml.safe_load(f) or {})
            except (yaml.YAMLError, FileNotFoundError, PermissionError) as e:
                print(f"Warning: Could not load config file: {e}")

        # Load secure configuration
        if self.secure_config_file.exists():
            try:
                with open(self.secure_config_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                secure_config = json.loads(decrypted_data.decode())
                config.update(secure_config)
            except Exception as e:
                print(f"Warning: Could not decrypt secure config: {e}")

        # Load environment variables
        config.update(self._load_env_config())
        
        # Load project-level configuration from .smart/
        config.update(self._load_project_config())

        return config

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # Map of config keys to environment variables
        env_mappings = {
            "openrouter_api_key": "OPENROUTER_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "github_token": "GITHUB_TOKEN",
            "redis_url": "REDIS_URL",
            "database_url": "DATABASE_URL",
            "log_level": "LOG_LEVEL",
            "cache_ttl": "CACHE_TTL",
            "max_tokens": "MAX_TOKENS",
            "temperature": "TEMPERATURE",
        }

        for config_key, env_var in env_mappings.items():
            if env_var in os.environ:
                env_config[config_key] = os.environ[env_var]

        return env_config

    def _load_project_config(self) -> Dict[str, Any]:
        """Load project-level configuration from .smart/ directory."""
        project_config = {}
        
        try:
            # Look for .smart/budget.json in current directory
            smart_dir = Path(".smart")
            budget_file = smart_dir / "budget.json"
            
            if budget_file.exists():
                import json
                with open(budget_file, "r") as f:
                    budget_data = json.load(f)
                
                # Map budget settings to config keys
                budget_mappings = {
                    "AI_DAILY_LIMIT": "daily_budget",
                    "AI_MONTHLY_LIMIT": "monthly_budget", 
                    "AI_REQUEST_LIMIT": "request_budget",
                    "AI_EMERGENCY_RESERVE": "emergency_reserve",
                    "BUDGET_PROFILE": "budget_profile"
                }
                
                for budget_key, config_key in budget_mappings.items():
                    if budget_key in budget_data:
                        try:
                            # Convert to float for numeric values
                            if budget_key != "BUDGET_PROFILE":
                                project_config[config_key] = float(budget_data[budget_key])
                            else:
                                project_config[config_key] = budget_data[budget_key]
                        except (ValueError, TypeError):
                            pass  # Skip invalid values
                            
        except Exception:
            pass  # Silently ignore project config errors
        
        return project_config

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any, secure: bool = False):
        """Set configuration value."""
        self.config[key] = value

        if secure:
            self._save_secure_config()
        else:
            self._save_config()

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self.config.copy()

    def _save_config(self):
        """Save general configuration to file."""
        # Separate secure and general config
        general_config = {}
        secure_keys = {
            "openrouter_api_key",
            "anthropic_api_key",
            "openai_api_key",
            "github_token",
            "database_url",
        }

        for key, value in self.config.items():
            if key not in secure_keys:
                general_config[key] = value

        with open(self.config_file, "w") as f:
            yaml.dump(general_config, f, default_flow_style=False)

    def _save_secure_config(self):
        """Save secure configuration to encrypted file."""
        secure_config = {}
        secure_keys = {
            "openrouter_api_key",
            "anthropic_api_key",
            "openai_api_key",
            "github_token",
            "database_url",
        }

        for key, value in self.config.items():
            if key in secure_keys:
                secure_config[key] = value

        if secure_config:
            encrypted_data = self.cipher.encrypt(json.dumps(secure_config).encode())
            with open(self.secure_config_file, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            os.chmod(self.secure_config_file, 0o600)

    def delete_config(self, key: str):
        """Delete configuration key."""
        if key in self.config:
            del self.config[key]
            self._save_config()
            self._save_secure_config()

    def reset_config(self):
        """Reset all configuration."""
        self.config.clear()

        # Remove config files
        if self.config_file.exists():
            self.config_file.unlink()
        if self.secure_config_file.exists():
            self.secure_config_file.unlink()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "log_level": "INFO",
            "cache_ttl": 3600,
            "max_tokens": 4000,
            "temperature": 0.7,
            "default_model": "anthropic/claude-3-sonnet-20240229",
            "fallback_models": [
                "anthropic/claude-3-sonnet-20240229",
                "openai/gpt-4-turbo",
                "google/gemini-pro",
            ],
            "timeout": 30,
            "max_retries": 3,
            "cache_enabled": True,
            "database": {
                "url": "postgresql://smartcli:smartcli123@localhost:5432/smartcli",
                "pool_size": 10,
                "max_overflow": 5,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
            },
            "redis": {
                "url": "redis://localhost:6379/0",
                "pool_size": 10,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True,
                "health_check_interval": 30,
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 8001,
                "health_check_enabled": True,
                "prometheus_enabled": True,
            },
        }

    def load_config_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_file}")
            return {}

        try:
            with open(config_path, "r") as f:
                content = f.read()

                # Replace environment variables in the content
                content = self._substitute_env_vars(content)

                config = yaml.safe_load(content) or {}
                logging.info(f"Loaded configuration from: {config_file}")
                return config
        except Exception as e:
            logging.error(f"Failed to load configuration file {config_file}: {e}")
            return {}

    def _substitute_env_vars(self, content: str) -> str:
        """Substitute environment variables in configuration content."""
        import re

        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default_value)

        # Replace ${VAR_NAME} and ${VAR_NAME:-default}
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"
        return re.sub(pattern, replace_env_var, content)

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        merged = {}
        for config in configs:
            self._deep_merge(merged, config)
        return merged

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target."""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration."""
        return self.config.get("database", self.get_default_config()["database"])

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis-specific configuration."""
        return self.config.get("redis", self.get_default_config()["redis"])

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring-specific configuration."""
        return self.config.get("monitoring", self.get_default_config()["monitoring"])

    def validate_config(self) -> bool:
        """Validate configuration completeness and correctness."""
        errors = []
        warnings = []
        
        # Check required basic configuration
        required_keys = {
            "default_model": str,
            "max_tokens": int, 
            "temperature": float
        }
        
        for key, expected_type in required_keys.items():
            value = self.config.get(key)
            if value is None:
                # Use defaults for missing values
                defaults = self.get_default_config()
                self.config[key] = defaults.get(key)
                warnings.append(f"Using default value for {key}: {self.config[key]}")
            else:
                # Validate type
                try:
                    if expected_type == int:
                        self.config[key] = int(value)
                    elif expected_type == float:
                        self.config[key] = float(value)
                    elif expected_type == str:
                        self.config[key] = str(value)
                except (ValueError, TypeError):
                    errors.append(f"Invalid type for {key}: expected {expected_type.__name__}, got {type(value).__name__}")
        
        # Validate value ranges
        if self.config.get("max_tokens", 0) < 1 or self.config.get("max_tokens", 0) > 32000:
            warnings.append("max_tokens should be between 1 and 32000")
            
        if self.config.get("temperature", 0) < 0 or self.config.get("temperature", 0) > 2:
            warnings.append("temperature should be between 0 and 2")
        
        # Validate API keys if present
        api_keys = ["openrouter_api_key", "anthropic_api_key", "openai_api_key"]
        has_api_key = False
        for key in api_keys:
            if self.config.get(key):
                has_api_key = True
                api_key = self.config[key]
                if len(api_key) < 10:
                    warnings.append(f"{key} seems too short")
                elif not api_key.startswith(("sk-", "api-", "ghp_", "github_pat_")):
                    warnings.append(f"{key} format might be incorrect")
        
        if not has_api_key:
            warnings.append("No API keys configured - AI features will be limited")
        
        # Validate model name
        model = self.config.get("default_model", "")
        if model and "/" not in model and not model.startswith(("gpt-", "claude-", "gemini-")):
            warnings.append(f"Model name '{model}' might be incorrect format")
        
        # Log validation results
        for warning in warnings:
            logging.warning(f"Config validation: {warning}")
        
        for error in errors:
            logging.error(f"Config validation: {error}")
        
        # Return True if no critical errors
        return len(errors) == 0
    
    def get_validation_report(self) -> dict:
        """Get detailed validation report."""
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config_status": {}
        }
        
        # Check API configuration
        api_keys = {
            "openrouter_api_key": "OpenRouter API",
            "anthropic_api_key": "Anthropic API", 
            "openai_api_key": "OpenAI API",
            "github_token": "GitHub Integration"
        }
        
        for key, description in api_keys.items():
            value = self.config.get(key)
            if value:
                report["config_status"][description] = "✅ Configured"
            else:
                report["config_status"][description] = "❌ Not configured"
        
        # Check core settings
        core_settings = {
            "default_model": self.config.get("default_model", "Not set"),
            "max_tokens": self.config.get("max_tokens", "Not set"),
            "temperature": self.config.get("temperature", "Not set"),
            "log_level": self.config.get("log_level", "INFO")
        }
        
        for setting, value in core_settings.items():
            report["config_status"][f"Core/{setting}"] = f"✅ {value}"
        
        # Validate and add warnings
        if not any(self.config.get(key) for key in ["openrouter_api_key", "anthropic_api_key"]):
            report["warnings"].append("No AI API keys configured")
            
        if not self.config.get("github_token"):
            report["warnings"].append("GitHub integration not configured")
        
        report["valid"] = len(report["errors"]) == 0
        return report
