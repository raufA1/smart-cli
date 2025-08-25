"""Tests for main CLI functionality."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, Mock

from src.cli import app


class TestMainCLI:
    """Test main CLI commands."""
    
    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'Smart CLI' in result.stdout
        assert 'AI-powered CLI tool' in result.stdout
    
    def test_version_command(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(app, ['version'])
        assert result.exit_code == 0
        assert 'Version' in result.stdout
        assert '1.0.0' in result.stdout
    
    def test_config_show_command(self, cli_runner, mock_config_manager):
        """Test config show command."""
        with patch('src.cli.ConfigManager', return_value=mock_config_manager):
            result = cli_runner.invoke(app, ['config', '--show'])
            assert result.exit_code == 0
            assert 'Configuration' in result.stdout
    
    def test_config_set_command(self, cli_runner):
        """Test config set command."""
        with patch('src.cli.ConfigManager') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            result = cli_runner.invoke(app, ['config', '--set', 'test_key', '--value', 'test_value'])
            assert result.exit_code == 0
            
            mock_config.set_config.assert_called_once_with('test_key', 'test_value')
    
    @pytest.mark.asyncio
    async def test_health_command(self, cli_runner):
        """Test health command."""
        with patch('src.utils.health_checker.HealthChecker') as mock_health_class:
            # Mock the health checker
            mock_health = Mock()
            mock_health.run_health_checks = Mock(return_value={
                'status': 'healthy',
                'checks': {
                    'python': {'status': 'healthy', 'details': {'version': '3.11.0'}},
                    'config': {'status': 'healthy', 'details': {'config_files': True}},
                }
            })
            mock_health_class.return_value = mock_health
            
            result = cli_runner.invoke(app, ['health'])
            assert result.exit_code == 0
            # Note: The actual async behavior might need more sophisticated mocking
    
    def test_invalid_command(self, cli_runner):
        """Test invalid command handling."""
        result = cli_runner.invoke(app, ['invalid-command'])
        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @pytest.mark.integration
    def test_full_cli_workflow(self, cli_runner, temp_dir):
        """Test a complete CLI workflow."""
        # This would test a real workflow like:
        # 1. Initialize project
        # 2. Generate code
        # 3. Review code
        # For now, just test that commands don't crash
        
        # Test init command exists
        result = cli_runner.invoke(app, ['init', '--help'])
        assert result.exit_code == 0
        
        # Test generate command exists
        result = cli_runner.invoke(app, ['generate', '--help'])
        assert result.exit_code == 0
        
        # Test review command exists
        result = cli_runner.invoke(app, ['review', '--help'])
        assert result.exit_code == 0
    
    @pytest.mark.integration
    def test_config_persistence(self, cli_runner, temp_config_dir):
        """Test that configuration persists between commands."""
        with patch('src.utils.config.Path.home', return_value=temp_config_dir.parent):
            # Set a config value
            result1 = cli_runner.invoke(app, ['config', '--set', 'test_key', '--value', 'test_value'])
            assert result1.exit_code == 0
            
            # Verify it persists (this would need actual file checking)
            result2 = cli_runner.invoke(app, ['config', '--show'])
            assert result2.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    def test_keyboard_interrupt(self, cli_runner):
        """Test KeyboardInterrupt handling."""
        with patch('src.cli.app') as mock_app:
            mock_app.side_effect = KeyboardInterrupt()
            
            # This is tricky to test directly, but we can test the main function
            from src.cli import main
            with pytest.raises(SystemExit):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_with(0)
    
    def test_general_exception(self, cli_runner):
        """Test general exception handling."""
        with patch('src.cli.app') as mock_app:
            mock_app.side_effect = Exception("Test error")
            
            from src.cli import main
            with pytest.raises(SystemExit):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_with(1)
    
    def test_missing_required_args(self, cli_runner):
        """Test handling of missing required arguments."""
        # Test commands that require arguments
        result = cli_runner.invoke(app, ['init', 'project'])
        # Should fail because project name is required
        assert result.exit_code != 0


class TestCLIPerformance:
    """Test CLI performance aspects."""
    
    @pytest.mark.slow
    def test_cli_startup_time(self, cli_runner):
        """Test CLI startup performance."""
        import time
        
        start_time = time.time()
        result = cli_runner.invoke(app, ['--help'])
        end_time = time.time()
        
        assert result.exit_code == 0
        startup_time = end_time - start_time
        
        # CLI should start quickly (less than 2 seconds)
        assert startup_time < 2.0, f"CLI startup too slow: {startup_time}s"
    
    @pytest.mark.slow
    def test_large_config_handling(self, cli_runner, temp_config_dir):
        """Test handling of large configuration files."""
        # Create a large config file and test performance
        large_config = {f'key_{i}': f'value_{i}' for i in range(1000)}
        
        with patch('src.utils.config.ConfigManager') as mock_config_class:
            mock_config = Mock()
            mock_config.get_all_config.return_value = large_config
            mock_config_class.return_value = mock_config
            
            import time
            start_time = time.time()
            result = cli_runner.invoke(app, ['config', '--show'])
            end_time = time.time()
            
            assert result.exit_code == 0
            processing_time = end_time - start_time
            
            # Should handle large configs efficiently
            assert processing_time < 1.0, f"Large config processing too slow: {processing_time}s"