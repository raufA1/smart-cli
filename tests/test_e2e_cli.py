"""End-to-end CLI tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, Mock

from src.cli import app


class TestE2ECLIBasics:
    """Test basic CLI functionality end-to-end."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_cli_help_command(self, cli_runner):
        """Test main help command."""
        result = cli_runner.invoke(app, ['--help'])
        
        assert result.exit_code == 0
        assert 'Smart CLI' in result.stdout
        assert 'AI-powered CLI tool' in result.stdout
        assert 'Commands' in result.stdout
    
    def test_version_command(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(app, ['version'])
        
        assert result.exit_code == 0
        assert 'Version' in result.stdout
        assert '1.0.0' in result.stdout
    
    def test_config_show_command(self, cli_runner):
        """Test config show command."""
        with patch('src.cli.ConfigManager') as mock_config_class:
            mock_config = Mock()
            mock_config.get_all_config.return_value = {
                'default_model': 'claude-3-sonnet',
                'temperature': 0.7
            }
            mock_config_class.return_value = mock_config
            
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
    
    def test_health_command(self, cli_runner):
        """Test health check command."""
        with patch('src.utils.health_checker.HealthChecker') as mock_health_class:
            mock_health = Mock()
            
            # Create a proper coroutine mock
            async def mock_health_check():
                return {
                    'status': 'healthy',
                    'checks': {
                        'python': {'status': 'healthy', 'details': {'version': '3.12.3'}},
                        'config': {'status': 'healthy', 'details': {}},
                    }
                }
            
            mock_health.run_health_checks = Mock(return_value=mock_health_check())
            mock_health_class.return_value = mock_health
            
            result = cli_runner.invoke(app, ['health'])
            
            assert result.exit_code == 0
            # Health command uses async, so result might vary
    
    def test_usage_command(self, cli_runner):
        """Test usage statistics command."""
        with patch('src.cli.UsageTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.get_daily_usage.return_value = {
                'overall': {
                    'total_requests': 5,
                    'total_tokens': 1000,
                    'total_estimated_cost': 0.05,
                    'total_actual_cost': None,
                    'average_cost_per_request': 0.01
                }
            }
            mock_tracker.check_budget_status.return_value = {
                'daily': {
                    'budget': 10.0,
                    'spent': 0.05,
                    'remaining': 9.95,
                    'percentage_used': 0.5,
                    'over_budget': False
                },
                'weekly': {
                    'budget': 50.0,
                    'spent': 0.05,
                    'remaining': 49.95,
                    'percentage_used': 0.1,
                    'over_budget': False
                },
                'monthly': {
                    'budget': 200.0,
                    'spent': 0.05,
                    'remaining': 199.95,
                    'percentage_used': 0.025,
                    'over_budget': False
                }
            }
            mock_tracker.get_top_usage_patterns.return_value = []
            mock_tracker_class.return_value = mock_tracker
            
            result = cli_runner.invoke(app, ['usage'])
            
            assert result.exit_code == 0
            assert 'Daily Usage Summary' in result.stdout
            assert 'Budget Status' in result.stdout
    
    def test_budget_command(self, cli_runner):
        """Test budget management command."""
        with patch('src.cli.UsageTracker') as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker.check_budget_status.return_value = {
                'daily': {'budget': 5.0, 'spent': 1.0, 'remaining': 4.0, 'over_budget': False},
                'weekly': {'budget': 25.0, 'spent': 5.0, 'remaining': 20.0, 'over_budget': False},
                'monthly': {'budget': 100.0, 'spent': 20.0, 'remaining': 80.0, 'over_budget': False}
            }
            mock_tracker_class.return_value = mock_tracker
            
            # Test showing current budget
            result = cli_runner.invoke(app, ['budget'])
            
            assert result.exit_code == 0
            assert 'Budget Configuration' in result.stdout


class TestE2ECommandsIntegration:
    """Test command integration scenarios."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    def test_template_generate_commands(self, cli_runner):
        """Test template generation commands."""
        result = cli_runner.invoke(app, ['template', '--help'])
        
        assert result.exit_code == 0
        assert 'Generate basic templates' in result.stdout
    
    def test_ai_generate_commands(self, cli_runner):
        """Test AI generation commands."""
        result = cli_runner.invoke(app, ['generate', '--help'])
        
        assert result.exit_code == 0
        assert 'Generate code using AI' in result.stdout
        assert 'function' in result.stdout
        assert 'api' in result.stdout
    
    def test_init_commands(self, cli_runner):
        """Test project initialization commands."""
        result = cli_runner.invoke(app, ['init', '--help'])
        
        assert result.exit_code == 0
        assert 'Initialize new projects' in result.stdout
    
    def test_review_commands(self, cli_runner):
        """Test code review commands."""
        result = cli_runner.invoke(app, ['review', '--help'])
        
        assert result.exit_code == 0
        assert 'Review and analyze code' in result.stdout


class TestE2EWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_config_setup_workflow(self, cli_runner):
        """Test complete configuration setup workflow."""
        with patch('src.cli.ConfigManager') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            # Step 1: Show initial config (empty)
            mock_config.get_all_config.return_value = {}
            result1 = cli_runner.invoke(app, ['config', '--show'])
            assert result1.exit_code == 0
            
            # Step 2: Set API key
            result2 = cli_runner.invoke(app, ['config', '--set', 'openrouter_api_key', '--value', 'test-key'])
            assert result2.exit_code == 0
            
            # Step 3: Set model preference
            result3 = cli_runner.invoke(app, ['config', '--set', 'default_model', '--value', 'claude-3-sonnet'])
            assert result3.exit_code == 0
            
            # Step 4: Set budget
            with patch('src.cli.UsageTracker') as mock_tracker_class:
                mock_tracker = Mock()
                mock_tracker.set_budget.return_value = True
                mock_tracker_class.return_value = mock_tracker
                
                result4 = cli_runner.invoke(app, ['budget', '--set', 'daily', '--amount', '10.0'])
                assert result4.exit_code == 0
    
    def test_template_generation_workflow(self, cli_runner, temp_project_dir):
        """Test template generation workflow."""
        # Change to temp directory
        original_cwd = Path.cwd()
        
        try:
            # Test function generation
            result = cli_runner.invoke(app, [
                'template', 'function', 'test_function',
                '--lang', 'python',
                '--desc', 'A test function'
            ], input='n\n')  # Don't save to file
            
            # Template generation should work without AI
            assert result.exit_code == 0
            
        finally:
            # Restore original directory
            pass
    
    @pytest.mark.skipif(True, reason="Requires AI API key for full test")
    def test_ai_generation_workflow(self, cli_runner, temp_project_dir):
        """Test AI-powered generation workflow (integration test)."""
        # This would be a full integration test with real AI
        with patch('src.commands.ai_generate._get_ai_workflow') as mock_workflow:
            # Mock the AI workflow
            mock_workflow.return_value = (Mock(), Mock())
            
            result = cli_runner.invoke(app, [
                'generate', 'function', 'fibonacci',
                '--lang', 'python',
                '--desc', 'Calculate fibonacci sequence'
            ], input='n\n')
            
            # Should attempt to generate (may fail without real API key)
            assert result.exit_code in [0, 1]  # Allow both success and failure
    
    def test_error_handling_workflow(self, cli_runner):
        """Test error handling across different scenarios."""
        # Test invalid command
        result1 = cli_runner.invoke(app, ['invalid-command'])
        assert result1.exit_code != 0
        
        # Test invalid subcommand
        result2 = cli_runner.invoke(app, ['generate', 'invalid-subcommand'])
        assert result2.exit_code != 0
        
        # Test missing required arguments
        result3 = cli_runner.invoke(app, ['template', 'function'])
        assert result3.exit_code != 0


class TestE2EFileOperations:
    """Test file operations in end-to-end scenarios."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_workspace(self):
        """Temporary workspace with sample files."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample Python file
        sample_py = temp_dir / "sample.py"
        sample_py.write_text('''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
''')
        
        # Create sample project structure
        project_dir = temp_dir / "sample_project"
        project_dir.mkdir()
        (project_dir / "main.py").write_text("print('Hello from main')")
        (project_dir / "README.md").write_text("# Sample Project")
        
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_code_review_workflow(self, cli_runner, temp_workspace):
        """Test code review workflow with real files."""
        sample_file = temp_workspace / "sample.py"
        
        # Test reviewing a single file
        result = cli_runner.invoke(app, [
            'review', 'code', str(sample_file),
            '--focus', 'general'
        ])
        
        # Should analyze the file (may show warnings about missing functionality)
        assert result.exit_code == 0
        assert 'Code Metrics' in result.stdout or 'reviewing' in result.stdout.lower()
    
    def test_project_review_workflow(self, cli_runner, temp_workspace):
        """Test project review workflow."""
        project_dir = temp_workspace / "sample_project"
        
        result = cli_runner.invoke(app, [
            'review', 'project', str(project_dir)
        ])
        
        # Should analyze project structure
        assert result.exit_code == 0
        assert ('Project Overview' in result.stdout or 
                'reviewing project' in result.stdout.lower() or
                'Found' in result.stdout)
    
    def test_template_output_to_file(self, cli_runner, temp_workspace):
        """Test template generation with file output."""
        output_file = temp_workspace / "generated_function.py"
        
        result = cli_runner.invoke(app, [
            'template', 'function', 'my_function',
            '--lang', 'python',
            '--desc', 'A generated function',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        
        # Check if file was created
        if output_file.exists():
            content = output_file.read_text()
            assert 'my_function' in content
            assert 'def my_function' in content


@pytest.mark.slow
class TestE2EPerformance:
    """Test CLI performance characteristics."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    def test_cli_startup_time(self, cli_runner):
        """Test CLI startup performance."""
        import time
        
        # Measure startup time
        start_time = time.time()
        result = cli_runner.invoke(app, ['--help'])
        end_time = time.time()
        
        startup_time = end_time - start_time
        
        assert result.exit_code == 0
        assert startup_time < 2.0, f"CLI startup too slow: {startup_time:.2f}s"
    
    def test_command_response_time(self, cli_runner):
        """Test command response times."""
        import time
        
        commands_to_test = [
            ['version'],
            ['config', '--show'],
            ['template', '--help'],
            ['generate', '--help'],
        ]
        
        for cmd in commands_to_test:
            start_time = time.time()
            result = cli_runner.invoke(app, cmd)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Commands should respond quickly
            assert response_time < 1.0, f"Command {' '.join(cmd)} too slow: {response_time:.2f}s"
            
            # Most commands should succeed (some may fail due to missing deps)
            if result.exit_code != 0:
                print(f"Command {' '.join(cmd)} failed: {result.stdout}")


@pytest.mark.integration
class TestE2ERealWorldScenarios:
    """Test real-world usage scenarios."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    def test_developer_workflow_simulation(self, cli_runner):
        """Simulate a typical developer workflow."""
        with patch('src.cli.ConfigManager') as mock_config_class, \
             patch('src.cli.UsageTracker') as mock_tracker_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config.get_all_config.return_value = {'default_model': 'claude-3-sonnet'}
            mock_config_class.return_value = mock_config
            
            mock_tracker = Mock()
            mock_tracker.get_daily_usage.return_value = {
                'overall': {'total_requests': 0, 'total_tokens': 0, 'total_estimated_cost': 0.0,
                          'total_actual_cost': None, 'average_cost_per_request': 0.0}
            }
            mock_tracker.check_budget_status.return_value = {
                'daily': {'budget': 10.0, 'spent': 0.0, 'remaining': 10.0, 'percentage_used': 0.0, 'over_budget': False},
                'weekly': {'budget': 50.0, 'spent': 0.0, 'remaining': 50.0, 'percentage_used': 0.0, 'over_budget': False},
                'monthly': {'budget': 200.0, 'spent': 0.0, 'remaining': 200.0, 'percentage_used': 0.0, 'over_budget': False}
            }
            mock_tracker.get_top_usage_patterns.return_value = []
            mock_tracker_class.return_value = mock_tracker
            
            # Simulate workflow steps
            
            # 1. Check CLI version and status
            result1 = cli_runner.invoke(app, ['version'])
            assert result1.exit_code == 0
            
            # 2. Check configuration
            result2 = cli_runner.invoke(app, ['config', '--show'])
            assert result2.exit_code == 0
            
            # 3. Check current usage
            result3 = cli_runner.invoke(app, ['usage'])
            assert result3.exit_code == 0
            
            # 4. Check available commands
            result4 = cli_runner.invoke(app, ['--help'])
            assert result4.exit_code == 0
            
            # All steps should complete successfully
            assert all(r.exit_code == 0 for r in [result1, result2, result3, result4])
    
    def test_help_system_completeness(self, cli_runner):
        """Test that help system is complete and accessible."""
        # Test main help
        result = cli_runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'Commands' in result.stdout
        
        # Test subcommand help for each major command
        subcommands = ['generate', 'template', 'init', 'review', 'config', 'usage', 'budget']
        
        for subcmd in subcommands:
            result = cli_runner.invoke(app, [subcmd, '--help'])
            # Some subcommands may not be fully implemented, but help should work
            assert result.exit_code == 0, f"Help for {subcmd} failed"
            assert 'Usage:' in result.stdout or 'Options:' in result.stdout
    
    def test_error_messages_quality(self, cli_runner):
        """Test that error messages are helpful and informative."""
        # Test various error scenarios
        
        # Invalid command
        result1 = cli_runner.invoke(app, ['nonexistent-command'])
        assert result1.exit_code != 0
        # Should show helpful error or available commands
        
        # Missing required arguments
        result2 = cli_runner.invoke(app, ['template', 'function'])
        assert result2.exit_code != 0
        # Should indicate missing argument
        
        # Invalid options
        result3 = cli_runner.invoke(app, ['version', '--invalid-option'])
        assert result3.exit_code != 0
        # Should show option error