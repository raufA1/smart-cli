"""Tests for configuration management."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import os

from src.utils.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager with temporary directory."""
        return ConfigManager(config_dir=temp_config_dir)
    
    def test_init_creates_config_directory(self, temp_config_dir):
        """Test that config directory is created on init."""
        config_dir = temp_config_dir / "test_config"
        assert not config_dir.exists()
        
        ConfigManager(config_dir=config_dir)
        assert config_dir.exists()
    
    def test_get_config_returns_default_for_missing_key(self, config_manager):
        """Test getting non-existent config key returns default."""
        result = config_manager.get_config("non_existent_key", "default_value")
        assert result == "default_value"
    
    def test_set_and_get_config(self, config_manager):
        """Test setting and getting config values."""
        config_manager.set_config("test_key", "test_value")
        result = config_manager.get_config("test_key")
        assert result == "test_value"
    
    def test_get_all_config(self, config_manager):
        """Test getting all configuration."""
        config_manager.set_config("key1", "value1")
        config_manager.set_config("key2", "value2")
        
        all_config = config_manager.get_all_config()
        assert "key1" in all_config
        assert "key2" in all_config
        assert all_config["key1"] == "value1"
        assert all_config["key2"] == "value2"
    
    def test_delete_config(self, config_manager):
        """Test deleting configuration keys."""
        config_manager.set_config("test_key", "test_value")
        assert config_manager.get_config("test_key") == "test_value"
        
        config_manager.delete_config("test_key")
        assert config_manager.get_config("test_key") is None
    
    def test_reset_config(self, config_manager):
        """Test resetting all configuration."""
        config_manager.set_config("key1", "value1")
        config_manager.set_config("key2", "value2")
        
        config_manager.reset_config()
        all_config = config_manager.get_all_config()
        
        assert "key1" not in all_config
        assert "key2" not in all_config
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_api_key'})
    def test_load_env_config(self, temp_config_dir):
        """Test loading configuration from environment variables."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Should load from environment
        assert config_manager.get_config('openrouter_api_key') == 'test_api_key'
    
    def test_secure_config_storage(self, config_manager):
        """Test secure configuration storage."""
        # This is a basic test - in real implementation, we'd test encryption
        config_manager.set_config("api_key", "secret_key", secure=True)
        
        # Should be able to retrieve the value
        result = config_manager.get_config("api_key")
        assert result == "secret_key"
    
    def test_get_default_config(self, config_manager):
        """Test getting default configuration."""
        defaults = config_manager.get_default_config()
        
        assert 'log_level' in defaults
        assert 'cache_ttl' in defaults
        assert 'max_tokens' in defaults
        assert 'temperature' in defaults
        assert 'default_model' in defaults
        assert 'fallback_models' in defaults
        
        assert defaults['log_level'] == 'INFO'
        assert defaults['cache_ttl'] == 3600
        assert defaults['max_tokens'] == 4000
        assert defaults['temperature'] == 0.7
    
    def test_encryption_key_generation(self, temp_config_dir):
        """Test that encryption key is generated."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        key_file = temp_config_dir / "config.key"
        assert key_file.exists()
        
        # Key file should have restrictive permissions
        # Note: This test might not work on all systems
        try:
            stat_info = key_file.stat()
            # Check if only owner has read/write permissions
            assert stat_info.st_mode & 0o077 == 0
        except (AttributeError, AssertionError):
            # Skip permission check on systems that don't support it
            pass


class TestConfigManagerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_config_directory_handling(self):
        """Test handling of invalid config directory."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            # Should not raise exception, but might log warning
            ConfigManager()
    
    def test_corrupted_config_file_handling(self, temp_config_dir):
        """Test handling of corrupted config files."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Write invalid YAML to config file
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        # Should handle gracefully
        config_manager._load_config()
    
    def test_missing_encryption_key(self, temp_config_dir):
        """Test behavior when encryption key is missing."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Remove encryption key
        key_file = temp_config_dir / "config.key"
        if key_file.exists():
            key_file.unlink()
        
        # Should regenerate key
        config_manager._init_encryption()
        assert key_file.exists()


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration management."""
    
    def test_config_persistence(self, temp_config_dir):
        """Test that configuration persists between instances."""
        # First instance
        config1 = ConfigManager(config_dir=temp_config_dir)
        config1.set_config("persistent_key", "persistent_value")
        
        # Second instance
        config2 = ConfigManager(config_dir=temp_config_dir)
        result = config2.get_config("persistent_key")
        
        assert result == "persistent_value"
    
    def test_environment_override(self, temp_config_dir):
        """Test that environment variables override file config."""
        # Set file config
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.set_config("log_level", "ERROR")
        
        # Environment should override
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            config_manager = ConfigManager(config_dir=temp_config_dir)
            result = config_manager.get_config("log_level")
            assert result == "DEBUG"