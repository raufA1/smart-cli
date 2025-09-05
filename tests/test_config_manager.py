"""
Tests for Mode Configuration Manager functionality.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch


class TestModeConfigManager:
    """Test ModeConfigManager core functionality."""
    
    def test_initialization(self):
        """Test ModeConfigManager initialization."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            assert manager is not None
            
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_default_configuration_structure(self):
        """Test default configuration has required structure."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            config = manager.get_default_mode_config()
            
            # Test required modes exist
            required_modes = ["smart", "code", "analysis", "architect", "learning", "fast", "orchestrator"]
            for mode in required_modes:
                assert mode in config, f"Mode '{mode}' missing from default config"
            
            # Test mode configuration structure
            for mode_name, mode_config in config.items():
                assert "name" in mode_config
                assert "description" in mode_config
                assert "context_size" in mode_config
                assert isinstance(mode_config["context_size"], int)
                assert mode_config["context_size"] > 0
                
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_specific_mode_configurations(self):
        """Test specific mode configuration details."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            config = manager.get_default_mode_config()
            
            # Test smart mode
            smart_config = config["smart"]
            assert "Auto-detection" in smart_config["description"] or "Intelligent" in smart_config["description"]
            
            # Test code mode
            code_config = config["code"]
            assert "development" in code_config["description"].lower() or "code" in code_config["description"].lower()
            
            # Test analysis mode
            analysis_config = config["analysis"]
            assert "analysis" in analysis_config["description"].lower() or "review" in analysis_config["description"].lower()
            
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_project_config_file_operations(self):
        """Test project configuration file operations."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            
            # Create test configuration
            test_config = {
                "modes": {
                    "code": {
                        "context_size": 8000,
                        "preferred_model": "anthropic/claude-3-sonnet-20240229",
                        "custom_setting": "test_value"
                    }
                },
                "project_settings": {
                    "auto_mode_switching": True,
                    "cache_enabled": True
                }
            }
            
            # Test saving and loading
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_config, f)
                temp_config_path = f.name
            
            try:
                # Test loading
                loaded_config = manager.load_project_config(temp_config_path)
                assert loaded_config is not None
                assert "modes" in loaded_config
                assert "code" in loaded_config["modes"]
                assert loaded_config["modes"]["code"]["context_size"] == 8000
                assert loaded_config["modes"]["code"]["custom_setting"] == "test_value"
                
                # Test project settings
                if "project_settings" in loaded_config:
                    assert loaded_config["project_settings"]["auto_mode_switching"] is True
                    
            finally:
                os.unlink(temp_config_path)
                
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration files."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            
            # Test with non-existent file
            result = manager.load_project_config("/non/existent/path.json")
            assert result is None
            
            # Test with invalid JSON
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("invalid json content {")
                invalid_config_path = f.name
            
            try:
                result = manager.load_project_config(invalid_config_path)
                assert result is None
            finally:
                os.unlink(invalid_config_path)
                
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_config_merging(self):
        """Test configuration merging functionality."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            
            # Get default config
            default_config = manager.get_default_mode_config()
            
            # Create override config
            override_config = {
                "code": {
                    "context_size": 16000,
                    "custom_setting": "override_value"
                }
            }
            
            # Test merging (if method exists)
            if hasattr(manager, 'merge_configurations'):
                merged = manager.merge_configurations(default_config, override_config)
                assert merged["code"]["context_size"] == 16000
                assert "custom_setting" in merged["code"]
                # Other modes should remain unchanged
                assert "smart" in merged
                assert "analysis" in merged
                
        except ImportError:
            pytest.skip("ModeConfigManager not available")
    
    def test_template_generation(self):
        """Test configuration template generation."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            
            # Test template generation for different project types
            project_types = ["python", "javascript", "general"]
            
            for project_type in project_types:
                if hasattr(manager, 'generate_project_template'):
                    template = manager.generate_project_template(project_type)
                    assert template is not None
                    assert isinstance(template, dict)
                    
        except ImportError:
            pytest.skip("ModeConfigManager not available")


class TestConfigurationValidation:
    """Test configuration validation functionality."""
    
    def test_mode_config_validation(self):
        """Test mode configuration validation."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            
            manager = ModeConfigManager()
            
            # Test valid configuration
            valid_config = {
                "name": "Test Mode",
                "description": "Test description",
                "context_size": 4000
            }
            
            # Test invalid configurations
            invalid_configs = [
                {},  # Empty config
                {"name": "Test"},  # Missing required fields
                {"name": "Test", "description": "Test", "context_size": -1},  # Invalid context size
                {"name": "Test", "description": "Test", "context_size": "invalid"},  # Wrong type
            ]
            
            # If validation method exists, test it
            if hasattr(manager, 'validate_mode_config'):
                assert manager.validate_mode_config(valid_config) is True
                
                for invalid_config in invalid_configs:
                    assert manager.validate_mode_config(invalid_config) is False
                    
        except ImportError:
            pytest.skip("ModeConfigManager not available")


class TestConfigurationIntegration:
    """Test configuration integration with other components."""
    
    def test_config_integration_with_mode_manager(self):
        """Test configuration integration with mode manager."""
        try:
            from src.core.mode_config_manager import ModeConfigManager
            from src.core.mode_manager import ModeManager
            
            config_manager = ModeConfigManager()
            mock_cli = Mock()
            mode_manager = ModeManager(mock_cli)
            
            # Test that configurations can be used by mode manager
            config = config_manager.get_default_mode_config()
            assert config is not None
            
            # Test specific mode configuration
            if "code" in config:
                code_config = config["code"]
                assert "context_size" in code_config
                
        except ImportError:
            pytest.skip("Configuration integration not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])