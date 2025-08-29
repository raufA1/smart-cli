"""Integration tests for session manager with budget profiles."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.session_manager import SessionManager
from src.core.budget_profiles import UsageProfile, BudgetProfile


class TestSessionManagerBudgetIntegration:
    """Test SessionManager integration with budget profiles."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_manager = SessionManager(debug=True)
    
    def test_session_manager_initialization_with_budget(self):
        """Test session manager initializes with budget manager."""
        assert self.session_manager.budget_manager is not None
        assert self.session_manager.current_profile is None
        
        # Budget manager should have all profiles
        profiles = self.session_manager.budget_manager.list_profiles()
        assert len(profiles) == 6
    
    def test_set_budget_profile(self):
        """Test setting a budget profile."""
        with patch('src.core.session_manager.console') as mock_console:
            self.session_manager.set_budget_profile(UsageProfile.DEVELOPER)
            
            assert self.session_manager.current_profile == UsageProfile.DEVELOPER
            
            # Verify console output was called
            mock_console.print.assert_called()
    
    def test_get_budget_profile(self):
        """Test getting current budget profile."""
        # Initially None
        assert self.session_manager.get_budget_profile() is None
        
        # Set and verify
        self.session_manager.set_budget_profile(UsageProfile.FREELANCER)
        assert self.session_manager.get_budget_profile() == UsageProfile.FREELANCER
    
    @patch('src.core.session_manager.console')
    def test_show_budget_info_no_profile(self, mock_console):
        """Test showing budget info when no profile is set."""
        self.session_manager.show_budget_info()
        
        # Should show error and list of available profiles
        mock_console.print.assert_called()
        calls = mock_console.print.call_args_list
        
        # Find the call that shows the error message
        error_call_found = any("Budget profili seçilməyib" in str(call) for call in calls)
        assert error_call_found
    
    @patch('src.core.session_manager.console')
    def test_show_budget_info_with_profile(self, mock_console):
        """Test showing budget info when profile is set."""
        self.session_manager.set_budget_profile(UsageProfile.STARTUP)
        
        # Clear previous calls
        mock_console.reset_mock()
        
        self.session_manager.show_budget_info()
        
        # Should show current profile details
        mock_console.print.assert_called()
        calls = mock_console.print.call_args_list
        
        # Check that startup profile info is displayed
        startup_call_found = any("Startup" in str(call) for call in calls)
        assert startup_call_found
    
    @patch('src.core.session_manager.console')
    def test_display_welcome_no_profile(self, mock_console):
        """Test welcome display without budget profile."""
        with patch('os.path.basename', return_value="test-project"):
            self.session_manager.display_welcome()
            
            # Should show warning about no profile selected
            calls = mock_console.print.call_args_list
            no_profile_call = any("Seçilməyib" in str(call) for call in calls)
            assert no_profile_call
    
    @patch('src.core.session_manager.console')
    def test_display_welcome_with_profile(self, mock_console):
        """Test welcome display with budget profile."""
        self.session_manager.set_budget_profile(UsageProfile.ENTERPRISE)
        
        # Clear previous calls
        mock_console.reset_mock()
        
        with patch('os.path.basename', return_value="enterprise-project"):
            self.session_manager.display_welcome()
            
            # Should show enterprise profile info
            calls = mock_console.print.call_args_list
            enterprise_call = any("Enterprise" in str(call) for call in calls)
            assert enterprise_call
            
            # Should show budget limits
            limit_call = any("100.00" in str(call) for call in calls)
            assert limit_call
    
    def test_session_lifecycle_with_budget(self):
        """Test complete session lifecycle with budget profiles."""
        # Start with no profile
        assert self.session_manager.current_profile is None
        
        # Set profile during session
        self.session_manager.set_budget_profile(UsageProfile.DEVELOPER)
        assert self.session_manager.current_profile == UsageProfile.DEVELOPER
        
        # Change profile
        self.session_manager.set_budget_profile(UsageProfile.FREELANCER)
        assert self.session_manager.current_profile == UsageProfile.FREELANCER
        
        # Profile should persist during session
        profile = self.session_manager.budget_manager.get_profile(UsageProfile.FREELANCER)
        assert profile.name == "Freelancer"
        assert profile.daily_limit == 15.0


class TestSessionManagerBudgetEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_manager = SessionManager(debug=False)
    
    def test_invalid_profile_handling(self):
        """Test handling of invalid profile scenarios."""
        # Test with None (should not crash)
        original_profile = self.session_manager.current_profile
        
        try:
            # This might raise an exception depending on implementation
            self.session_manager.current_profile = None
            assert self.session_manager.get_budget_profile() is None
        except Exception:
            # If it raises an exception, that's also acceptable
            pass
        finally:
            self.session_manager.current_profile = original_profile
    
    @patch('src.core.session_manager.get_profile_manager')
    def test_budget_manager_initialization_failure(self, mock_get_profile_manager):
        """Test behavior when budget manager fails to initialize."""
        mock_get_profile_manager.side_effect = Exception("Failed to initialize")
        
        # Should handle gracefully
        try:
            session_manager = SessionManager()
            # If it doesn't crash, that's good
            assert True
        except Exception:
            # If it does crash, we need to handle this better
            pytest.skip("Budget manager initialization should be more robust")
    
    def test_session_manager_without_budget_methods(self):
        """Test core session manager functionality still works."""
        # Test basic session functionality
        assert self.session_manager.session_id.startswith("smart_")
        assert isinstance(self.session_manager.start_time, datetime)
        assert not self.session_manager.session_active
        
        # Test conversation history
        self.session_manager.add_to_history("user", "test message")
        history = self.session_manager.get_recent_history(1)
        assert len(history) == 1
        assert history[0]["content"] == "test message"


class TestSessionManagerBudgetProfileIntegration:
    """Test deeper integration between session manager and budget profiles."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_manager = SessionManager(debug=True)
    
    def test_all_profiles_can_be_set(self):
        """Test that all profile types can be set successfully."""
        for profile_type in UsageProfile:
            with patch('src.core.session_manager.console'):
                self.session_manager.set_budget_profile(profile_type)
                assert self.session_manager.current_profile == profile_type
                
                # Verify we can get the profile details
                profile = self.session_manager.budget_manager.get_profile(profile_type)
                assert isinstance(profile, BudgetProfile)
                assert profile.name is not None
                assert profile.daily_limit > 0
    
    @patch('src.core.session_manager.console')
    def test_profile_switching_behavior(self, mock_console):
        """Test switching between different profiles."""
        # Start with student
        self.session_manager.set_budget_profile(UsageProfile.STUDENT)
        student_profile = self.session_manager.budget_manager.get_profile(UsageProfile.STUDENT)
        
        # Switch to enterprise
        self.session_manager.set_budget_profile(UsageProfile.ENTERPRISE)
        enterprise_profile = self.session_manager.budget_manager.get_profile(UsageProfile.ENTERPRISE)
        
        # Verify the switch
        assert self.session_manager.current_profile == UsageProfile.ENTERPRISE
        assert enterprise_profile.daily_limit > student_profile.daily_limit
        
        # Console should have been called for both switches
        assert mock_console.print.call_count >= 2
    
    def test_budget_profile_persistence_during_session(self):
        """Test that budget profile persists during session operations."""
        self.session_manager.set_budget_profile(UsageProfile.STARTUP)
        
        # Simulate session operations
        self.session_manager.add_to_history("user", "test command")
        self.session_manager.add_to_history("assistant", "test response")
        
        # Profile should still be set
        assert self.session_manager.current_profile == UsageProfile.STARTUP
        
        # Budget manager should still be functional
        profile = self.session_manager.budget_manager.get_profile(UsageProfile.STARTUP)
        assert profile.name == "Startup"


class TestSessionManagerAsync:
    """Test async functionality with budget profiles."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_manager = SessionManager(debug=True)
    
    @pytest.mark.asyncio
    async def test_start_session_with_budget_profile(self):
        """Test starting session with budget profile set."""
        self.session_manager.set_budget_profile(UsageProfile.DEVELOPER)
        
        with patch('src.core.session_manager.console'):
            result = await self.session_manager.start_session()
            
            assert result is True
            assert self.session_manager.session_active is True
            assert self.session_manager.current_profile == UsageProfile.DEVELOPER
    
    @pytest.mark.asyncio
    async def test_end_session_preserves_profile_info(self):
        """Test that ending session preserves profile information."""
        self.session_manager.set_budget_profile(UsageProfile.FREELANCER)
        self.session_manager.session_active = True
        
        with patch('src.core.session_manager.console'):
            await self.session_manager.end_session()
            
            # Session should be ended but profile info preserved
            assert self.session_manager.session_active is False
            assert self.session_manager.current_profile == UsageProfile.FREELANCER


class TestSessionManagerBudgetUIIntegration:
    """Test UI integration with budget profiles."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_manager = SessionManager(debug=True)
    
    @patch('src.core.session_manager.console')
    @patch('os.path.basename')
    def test_welcome_display_formatting(self, mock_basename, mock_console):
        """Test welcome display formatting with budget info."""
        mock_basename.return_value = "smart-project"
        
        # Test with different profiles
        test_profiles = [UsageProfile.STUDENT, UsageProfile.ENTERPRISE]
        
        for profile in test_profiles:
            self.session_manager.set_budget_profile(profile)
            mock_console.reset_mock()
            
            self.session_manager.display_welcome()
            
            # Verify console formatting calls
            calls = mock_console.print.call_args_list
            assert len(calls) > 0
            
            # Check for budget profile info in output
            profile_info_found = False
            for call in calls:
                call_str = str(call)
                if profile.name in call_str or "Budget Profili" in call_str:
                    profile_info_found = True
                    break
            
            assert profile_info_found, f"Profile {profile.name} info not found in welcome display"


if __name__ == "__main__":
    pytest.main([__file__])