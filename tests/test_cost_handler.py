"""Tests for cost handler and budget management CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
from pathlib import Path

from src.handlers.cost_handler import CostHandler
from src.core.budget_profiles import UsageProfile, BudgetProfile


class TestCostHandler:
    """Test CostHandler basic functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.mock_smart_cli.session_manager = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    def test_keywords(self):
        """Test cost handler keywords."""
        keywords = self.handler.keywords
        
        assert "cost" in keywords
        assert "budget" in keywords
        assert "usage" in keywords
        assert "xərc" in keywords  # Azerbaijani
        assert "büdcə" in keywords  # Azerbaijani
        
        assert len(keywords) > 5
    
    def test_matches_cost_command_direct(self):
        """Test matching direct cost commands."""
        test_cases = [
            ("cost status", True),
            ("budget status", True),
            ("usage report", True),
            ("spending report", True),
            ("cost limit", True),
            ("set budget", True),
            ("xərc hesabatı", True),
            ("büdcə vəziyyəti", True),
            ("hello world", False),
            ("test command", False),
        ]
        
        for command, expected in test_cases:
            result = self.handler._matches_cost_command(command)
            assert result == expected, f"Command '{command}' should return {expected}"
    
    def test_matches_cost_command_keywords(self):
        """Test matching cost commands by keywords."""
        test_cases = [
            ("show me the cost", True),
            ("what's my budget", True),
            ("check usage", True),
            ("price information", True),
            ("money spent", True),
            ("random text", False),
            ("help command", False),
        ]
        
        for command, expected in test_cases:
            result = self.handler._matches_cost_command(command)
            assert result == expected, f"Command '{command}' should return {expected}"
    
    @pytest.mark.asyncio
    async def test_handle_non_matching_command(self):
        """Test handling non-cost commands."""
        result = await self.handler.handle("hello world")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_handle_matching_command(self):
        """Test handling cost commands."""
        with patch.object(self.handler, '_process_cost_command') as mock_process:
            result = await self.handler.handle("cost status")
            
            assert result is True
            mock_process.assert_called_once_with("cost status")


class TestCostHandlerCommands:
    """Test specific cost handler command processing."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.mock_smart_cli.session_manager = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_cost_optimizer')
    @patch('src.handlers.cost_handler.console')
    async def test_show_cost_status(self, mock_console, mock_get_optimizer):
        """Test showing cost status."""
        # Mock cost optimizer
        mock_optimizer = Mock()
        mock_optimizer.get_budget_status.return_value = {
            'daily_usage': 2.5,
            'daily_limit': 10.0,
            'daily_remaining': 7.5,
            'daily_percentage': 25.0,
            'monthly_usage': 45.0,
            'monthly_limit': 200.0,
            'monthly_remaining': 155.0,
        }
        mock_get_optimizer.return_value = mock_optimizer
        
        await self.handler._process_cost_command("cost status")
        
        mock_optimizer.get_budget_status.assert_called_once()
        mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_cost_optimizer')
    @patch('src.handlers.cost_handler.console')
    async def test_show_model_pricing(self, mock_console, mock_get_optimizer):
        """Test showing model pricing."""
        # Mock cost optimizer with models
        mock_optimizer = Mock()
        mock_model = Mock()
        mock_model.provider = "OpenRouter"
        mock_model.cost_per_1k_input = 0.001
        mock_model.cost_per_1k_output = 0.002
        mock_model.tier = Mock()
        mock_model.tier.value = "premium"
        mock_model.strengths = ["coding", "analysis"]
        
        mock_optimizer.models = {"claude-sonnet": mock_model}
        mock_get_optimizer.return_value = mock_optimizer
        
        await self.handler._process_cost_command("cost models")
        
        mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_cost_optimizer')
    @patch('src.handlers.cost_handler.console')
    async def test_show_optimization_suggestions(self, mock_console, mock_get_optimizer):
        """Test showing optimization suggestions."""
        mock_optimizer = Mock()
        mock_optimizer.suggest_cost_optimization.return_value = [
            "Use cheaper models for simple tasks",
            "Enable caching for repeated requests"
        ]
        mock_get_optimizer.return_value = mock_optimizer
        
        await self.handler._process_cost_command("cost optimize")
        
        mock_optimizer.suggest_cost_optimization.assert_called_once()
        mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_show_cost_help(self, mock_console):
        """Test showing cost help."""
        await self.handler._show_cost_help()
        mock_console.print.assert_called()


class TestBudgetLimitSetting:
    """Test budget limit setting functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.mock_smart_cli.session_manager = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_cost_optimizer')
    @patch('src.handlers.cost_handler.console')
    async def test_set_daily_limit_valid(self, mock_console, mock_get_optimizer):
        """Test setting valid daily limit."""
        mock_optimizer = Mock()
        mock_optimizer.budget = Mock()
        mock_optimizer.budget.daily_limit = 5.0
        mock_get_optimizer.return_value = mock_optimizer
        
        with patch.object(self.handler, '_update_env_file') as mock_update_env:
            await self.handler._update_daily_limit(mock_optimizer, 15.0)
            
            assert mock_optimizer.budget.daily_limit == 15.0
            mock_update_env.assert_called_once_with("AI_DAILY_LIMIT", "15.0")
            mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_set_daily_limit_too_low(self, mock_console):
        """Test setting daily limit too low."""
        mock_optimizer = Mock()
        await self.handler._update_daily_limit(mock_optimizer, 0.25)
        
        # Should show warning about low limit
        warning_call = any("too low" in str(call) for call in mock_console.print.call_args_list)
        assert warning_call
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_set_daily_limit_too_high(self, mock_console):
        """Test setting daily limit very high."""
        mock_optimizer = Mock()
        mock_optimizer.budget = Mock()
        mock_optimizer.budget.daily_limit = 10.0
        
        with patch.object(self.handler, '_update_env_file'):
            await self.handler._update_daily_limit(mock_optimizer, 1500.0)
            
            # Should show warning about high limit
            warning_call = any("very high" in str(call) for call in mock_console.print.call_args_list)
            assert warning_call
    
    @pytest.mark.asyncio
    async def test_parse_budget_command_valid(self):
        """Test parsing valid budget commands."""
        test_cases = [
            ("cost set daily 10.00", 10.0),
            ("cost set daily 5.5", 5.5),
            ("cost set monthly 200", 200.0),
            ("cost set request 1.25", 1.25),
        ]
        
        for command, expected_amount in test_cases:
            with patch.object(self.handler, '_update_daily_limit') as mock_update:
                if "daily" in command:
                    with patch('src.handlers.cost_handler.get_cost_optimizer'):
                        await self.handler._set_budget_limits(Mock(), command)
                        mock_update.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_parse_budget_command_invalid_amount(self, mock_console):
        """Test parsing budget command with invalid amount."""
        mock_optimizer = Mock()
        await self.handler._set_budget_limits(mock_optimizer, "cost set daily invalid")
        
        # Should show error about specifying amount
        error_call = any("specify an amount" in str(call) for call in mock_console.print.call_args_list)
        assert error_call
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_parse_budget_command_no_type(self, mock_console):
        """Test parsing budget command without limit type."""
        mock_optimizer = Mock()
        await self.handler._set_budget_limits(mock_optimizer, "cost set 10.00")
        
        # Should show error about specifying limit type
        error_call = any("Specify limit type" in str(call) for call in mock_console.print.call_args_list)
        assert error_call


class TestEnvFileUpdates:
    """Test environment file update functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    @pytest.mark.asyncio
    async def test_update_env_file_new_key(self):
        """Test adding new key to env file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.env') as f:
            f.write("EXISTING_KEY=value1\n")
            f.write("ANOTHER_KEY=value2\n")
            env_file_path = f.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data="EXISTING_KEY=value1\nANOTHER_KEY=value2\n")) as mock_file:
                
                await self.handler._update_env_file("NEW_KEY", "new_value")
                
                # Verify file operations
                mock_file.assert_called()
        finally:
            os.unlink(env_file_path)
    
    @pytest.mark.asyncio
    async def test_update_env_file_existing_key(self):
        """Test updating existing key in env file."""
        original_content = "EXISTING_KEY=old_value\nANOTHER_KEY=value2\n"
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=original_content)) as mock_file:
            
            await self.handler._update_env_file("EXISTING_KEY", "new_value")
            
            # Verify file operations
            mock_file.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_update_env_file_not_found(self, mock_console):
        """Test handling missing env file."""
        with patch('pathlib.Path.exists', return_value=False):
            await self.handler._update_env_file("TEST_KEY", "test_value")
            
            # Should show warning about missing file
            warning_call = any("not found" in str(call) for call in mock_console.print.call_args_list)
            assert warning_call


class TestBudgetProfileCommands:
    """Test budget profile management commands."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.mock_smart_cli.session_manager = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_profile_manager')
    @patch('src.handlers.cost_handler.console')
    async def test_show_budget_profiles(self, mock_console, mock_get_profile_manager):
        """Test showing budget profiles."""
        mock_manager = Mock()
        mock_profile = Mock()
        mock_profile.name = "Developer"
        mock_profile.description = "For regular development work"
        mock_profile.daily_limit = 8.0
        mock_profile.monthly_limit = 180.0
        mock_profile.per_request_limit = 1.0
        
        mock_manager.list_profiles.return_value = {
            UsageProfile.DEVELOPER: mock_profile
        }
        mock_get_profile_manager.return_value = mock_manager
        
        await self.handler._show_budget_profiles(mock_manager)
        
        mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_profile_manager')
    @patch('src.handlers.cost_handler.console')
    async def test_apply_budget_profile_valid(self, mock_console, mock_get_profile_manager):
        """Test applying valid budget profile."""
        mock_manager = Mock()
        mock_profile = Mock()
        mock_profile.name = "Developer"
        mock_profile.daily_limit = 8.0
        mock_profile.monthly_limit = 180.0
        mock_profile.per_request_limit = 1.0
        
        mock_manager.get_profile_by_name.return_value = mock_profile
        mock_manager.list_profiles.return_value = {
            UsageProfile.DEVELOPER: mock_profile
        }
        mock_manager.apply_profile.return_value = {
            "AI_DAILY_LIMIT": "8.0",
            "AI_MONTHLY_LIMIT": "180.0"
        }
        mock_get_profile_manager.return_value = mock_manager
        
        with patch.object(self.handler, '_update_env_file') as mock_update_env:
            await self.handler._apply_budget_profile(mock_manager, "cost profile set developer")
            
            mock_manager.get_profile_by_name.assert_called_with("developer")
            mock_manager.apply_profile.assert_called()
            mock_update_env.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_profile_manager')
    @patch('src.handlers.cost_handler.console')
    async def test_apply_budget_profile_invalid(self, mock_console, mock_get_profile_manager):
        """Test applying invalid budget profile."""
        mock_manager = Mock()
        mock_manager.get_profile_by_name.side_effect = ValueError("Profile 'invalid' not found")
        mock_get_profile_manager.return_value = mock_manager
        
        await self.handler._apply_budget_profile(mock_manager, "cost profile set invalid")
        
        # Should show error message
        error_call = any("not found" in str(call) for call in mock_console.print.call_args_list)
        assert error_call
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_profile_manager')
    @patch('src.handlers.cost_handler.console')
    async def test_apply_budget_profile_no_name(self, mock_console, mock_get_profile_manager):
        """Test applying budget profile without specifying name."""
        mock_manager = Mock()
        mock_get_profile_manager.return_value = mock_manager
        
        await self.handler._apply_budget_profile(mock_manager, "cost profile set")
        
        # Should show error about specifying name
        error_call = any("specify a profile name" in str(call) for call in mock_console.print.call_args_list)
        assert error_call
    
    @pytest.mark.asyncio
    async def test_apply_profile_with_session_manager(self):
        """Test applying profile updates session manager."""
        mock_session_manager = Mock()
        self.mock_smart_cli.session_manager = mock_session_manager
        
        mock_manager = Mock()
        mock_profile = Mock()
        mock_profile.name = "Freelancer"
        mock_profile.daily_limit = 15.0
        mock_profile.monthly_limit = 350.0
        
        mock_manager.get_profile_by_name.return_value = mock_profile
        mock_manager.list_profiles.return_value = {
            UsageProfile.FREELANCER: mock_profile
        }
        mock_manager.apply_profile.return_value = {}
        
        with patch('src.handlers.cost_handler.get_profile_manager', return_value=mock_manager), \
             patch('src.handlers.cost_handler.console'), \
             patch.object(self.handler, '_update_env_file'):
            
            await self.handler._apply_budget_profile(mock_manager, "cost profile set freelancer")
            
            # Session manager should be updated
            mock_session_manager.set_budget_profile.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.get_profile_manager')
    @patch('src.handlers.cost_handler.console')
    async def test_compare_profiles(self, mock_console, mock_get_profile_manager):
        """Test comparing budget profiles."""
        mock_manager = Mock()
        mock_manager.get_cost_comparison.return_value = {
            "Student": {
                "daily_limit": 2.0,
                "monthly_limit": 40.0,
                "annual_cost_estimate": 480.0,
                "cost_per_1k_requests_estimate": 250.0
            },
            "Developer": {
                "daily_limit": 8.0,
                "monthly_limit": 180.0,
                "annual_cost_estimate": 2160.0,
                "cost_per_1k_requests_estimate": 1000.0
            }
        }
        mock_get_profile_manager.return_value = mock_manager
        
        await self.handler._compare_profiles(mock_manager)
        
        mock_console.print.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.handlers.cost_handler.console')
    async def test_recommend_profile(self, mock_console):
        """Test profile recommendation."""
        mock_manager = Mock()
        await self.handler._recommend_profile(mock_manager)
        
        mock_console.print.assert_called()


class TestCostHandlerIntegration:
    """Integration tests for cost handler."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_smart_cli = Mock()
        self.mock_smart_cli.session_manager = Mock()
        self.handler = CostHandler(self.mock_smart_cli)
    
    @pytest.mark.asyncio
    async def test_full_workflow_set_profile(self):
        """Test complete workflow of setting a budget profile."""
        with patch('src.handlers.cost_handler.get_profile_manager') as mock_get_manager, \
             patch('src.handlers.cost_handler.console') as mock_console, \
             patch.object(self.handler, '_update_env_file') as mock_update_env:
            
            # Setup mocks
            mock_manager = Mock()
            mock_profile = Mock()
            mock_profile.name = "Startup"
            mock_profile.daily_limit = 25.0
            mock_profile.monthly_limit = 600.0
            mock_profile.per_request_limit = 3.0
            
            mock_manager.get_profile_by_name.return_value = mock_profile
            mock_manager.list_profiles.return_value = {UsageProfile.STARTUP: mock_profile}
            mock_manager.apply_profile.return_value = {
                "AI_DAILY_LIMIT": "25.0",
                "AI_MONTHLY_LIMIT": "600.0",
                "AI_REQUEST_LIMIT": "3.0",
                "AI_EMERGENCY_RESERVE": "50.0",
                "BUDGET_PROFILE": "startup"
            }
            mock_get_manager.return_value = mock_manager
            
            # Test the workflow
            result = await self.handler.handle("cost profile set startup")
            
            # Verify result
            assert result is True
            mock_manager.get_profile_by_name.assert_called_with("startup")
            mock_manager.apply_profile.assert_called()
            self.mock_smart_cli.session_manager.set_budget_profile.assert_called()
            
            # Verify environment updates
            assert mock_update_env.call_count == 5  # 5 env vars to update


if __name__ == "__main__":
    pytest.main([__file__])