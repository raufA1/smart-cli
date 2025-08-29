"""Tests for budget profile management system."""

import pytest
from unittest.mock import Mock, patch

from src.core.budget_profiles import (
    BudgetProfile,
    BudgetProfileManager,
    UsageProfile,
    get_profile_manager
)


class TestBudgetProfile:
    """Test BudgetProfile dataclass."""
    
    def test_budget_profile_creation(self):
        """Test creating a budget profile."""
        profile = BudgetProfile(
            name="Test Profile",
            description="Test description",
            daily_limit=10.0,
            monthly_limit=300.0,
            per_request_limit=1.0,
            emergency_reserve=25.0,
            recommended_models={
                "analyzer": "claude-haiku",
                "modifier": "llama-3-8b"
            }
        )
        
        assert profile.name == "Test Profile"
        assert profile.description == "Test description"
        assert profile.daily_limit == 10.0
        assert profile.monthly_limit == 300.0
        assert profile.per_request_limit == 1.0
        assert profile.emergency_reserve == 25.0
        assert "analyzer" in profile.recommended_models
        assert profile.recommended_models["analyzer"] == "claude-haiku"


class TestBudgetProfileManager:
    """Test BudgetProfileManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.manager = BudgetProfileManager()
    
    def test_get_profile(self):
        """Test getting a profile by type."""
        student_profile = self.manager.get_profile(UsageProfile.STUDENT)
        
        assert student_profile.name == "Student"
        assert student_profile.daily_limit == 2.0
        assert student_profile.monthly_limit == 40.0
        assert "analyzer" in student_profile.recommended_models
    
    def test_list_profiles(self):
        """Test listing all profiles."""
        profiles = self.manager.list_profiles()
        
        assert len(profiles) == 6
        assert UsageProfile.STUDENT in profiles
        assert UsageProfile.DEVELOPER in profiles
        assert UsageProfile.FREELANCER in profiles
        assert UsageProfile.STARTUP in profiles
        assert UsageProfile.ENTERPRISE in profiles
        assert UsageProfile.UNLIMITED in profiles
    
    def test_get_profile_by_name_valid(self):
        """Test getting profile by valid name."""
        # Test with exact name
        profile = self.manager.get_profile_by_name("Developer")
        assert profile.name == "Developer"
        assert profile.daily_limit == 8.0
        
        # Test with lowercase
        profile = self.manager.get_profile_by_name("developer")
        assert profile.name == "Developer"
        
        # Test with enum value
        profile = self.manager.get_profile_by_name("freelancer")
        assert profile.name == "Freelancer"
        assert profile.daily_limit == 15.0
    
    def test_get_profile_by_name_invalid(self):
        """Test getting profile by invalid name."""
        with pytest.raises(ValueError, match="Profile 'invalid' not found"):
            self.manager.get_profile_by_name("invalid")
    
    def test_recommend_profile(self):
        """Test profile recommendation logic."""
        # Test student recommendation
        recommendation = self.manager.recommend_profile(1.5, 1)
        assert recommendation == UsageProfile.STUDENT
        
        # Test developer recommendation
        recommendation = self.manager.recommend_profile(6.0, 1)
        assert recommendation == UsageProfile.DEVELOPER
        
        # Test freelancer recommendation
        recommendation = self.manager.recommend_profile(12.0, 1)
        assert recommendation == UsageProfile.FREELANCER
        
        # Test startup recommendation
        recommendation = self.manager.recommend_profile(20.0, 1)
        assert recommendation == UsageProfile.STARTUP
        
        # Test enterprise recommendation
        recommendation = self.manager.recommend_profile(80.0, 1)
        assert recommendation == UsageProfile.ENTERPRISE
        
        # Test unlimited recommendation
        recommendation = self.manager.recommend_profile(150.0, 1)
        assert recommendation == UsageProfile.UNLIMITED
        
        # Test with team size multiplier
        recommendation = self.manager.recommend_profile(2.0, 3)  # 6.0 total
        assert recommendation == UsageProfile.DEVELOPER
    
    def test_apply_profile(self):
        """Test applying a profile to get environment variables."""
        env_vars = self.manager.apply_profile(UsageProfile.DEVELOPER)
        
        expected_keys = {
            "AI_DAILY_LIMIT",
            "AI_MONTHLY_LIMIT", 
            "AI_REQUEST_LIMIT",
            "AI_EMERGENCY_RESERVE",
            "BUDGET_PROFILE"
        }
        
        assert set(env_vars.keys()) == expected_keys
        assert env_vars["AI_DAILY_LIMIT"] == "8.0"
        assert env_vars["AI_MONTHLY_LIMIT"] == "180.0"
        assert env_vars["AI_REQUEST_LIMIT"] == "1.0"
        assert env_vars["AI_EMERGENCY_RESERVE"] == "15.0"
        assert env_vars["BUDGET_PROFILE"] == "developer"
    
    def test_get_cost_comparison(self):
        """Test cost comparison between profiles."""
        comparison = self.manager.get_cost_comparison()
        
        assert len(comparison) == 6
        assert "Student" in comparison
        assert "Enterprise" in comparison
        
        student_costs = comparison["Student"]
        assert student_costs["daily_limit"] == 2.0
        assert student_costs["monthly_limit"] == 40.0
        assert student_costs["annual_cost_estimate"] == 480.0  # 40 * 12
        assert student_costs["cost_per_1k_requests_estimate"] == 250.0  # 0.25 * 1000
        
        enterprise_costs = comparison["Enterprise"]
        assert enterprise_costs["daily_limit"] == 100.0
        assert enterprise_costs["monthly_limit"] == 2500.0


class TestProfileManagerSingleton:
    """Test global profile manager singleton."""
    
    def test_get_profile_manager_singleton(self):
        """Test that get_profile_manager returns the same instance."""
        manager1 = get_profile_manager()
        manager2 = get_profile_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, BudgetProfileManager)


class TestUsageProfileEnum:
    """Test UsageProfile enum."""
    
    def test_usage_profile_values(self):
        """Test enum values."""
        assert UsageProfile.STUDENT.value == "student"
        assert UsageProfile.DEVELOPER.value == "developer"
        assert UsageProfile.FREELANCER.value == "freelancer"
        assert UsageProfile.STARTUP.value == "startup"
        assert UsageProfile.ENTERPRISE.value == "enterprise"
        assert UsageProfile.UNLIMITED.value == "unlimited"
    
    def test_all_profiles_exist(self):
        """Test that all profile types have corresponding profiles."""
        manager = BudgetProfileManager()
        profiles = manager.list_profiles()
        
        for profile_type in UsageProfile:
            assert profile_type in profiles
            profile = profiles[profile_type]
            assert isinstance(profile, BudgetProfile)


class TestBudgetProfileValidation:
    """Test budget profile validation and edge cases."""
    
    def setup_method(self):
        """Setup test environment."""
        self.manager = BudgetProfileManager()
    
    def test_profile_limits_logical(self):
        """Test that profile limits are logically consistent."""
        for profile_type, profile in self.manager.list_profiles().items():
            # Monthly limit should be at least daily limit
            assert profile.monthly_limit >= profile.daily_limit
            
            # Per-request limit should not exceed daily limit
            assert profile.per_request_limit <= profile.daily_limit
            
            # Emergency reserve should be reasonable
            assert profile.emergency_reserve >= 0
            assert profile.emergency_reserve <= profile.monthly_limit
    
    def test_recommended_models_exist(self):
        """Test that all profiles have recommended models."""
        expected_agents = {"analyzer", "modifier", "architect", "tester", "reviewer"}
        
        for profile_type, profile in self.manager.list_profiles().items():
            # All profiles should have model recommendations
            assert len(profile.recommended_models) > 0
            
            # Check that important agents have recommendations
            for agent in expected_agents:
                if agent in profile.recommended_models:
                    assert isinstance(profile.recommended_models[agent], str)
                    assert len(profile.recommended_models[agent]) > 0
    
    def test_profile_progression(self):
        """Test that profiles progress logically from student to unlimited."""
        profiles = [
            self.manager.get_profile(UsageProfile.STUDENT),
            self.manager.get_profile(UsageProfile.DEVELOPER),
            self.manager.get_profile(UsageProfile.FREELANCER),
            self.manager.get_profile(UsageProfile.STARTUP),
            self.manager.get_profile(UsageProfile.ENTERPRISE),
            self.manager.get_profile(UsageProfile.UNLIMITED),
        ]
        
        # Daily limits should generally increase
        for i in range(1, len(profiles)):
            assert profiles[i].daily_limit >= profiles[i-1].daily_limit
        
        # Monthly limits should generally increase
        for i in range(1, len(profiles)):
            assert profiles[i].monthly_limit >= profiles[i-1].monthly_limit


class TestBudgetProfileIntegration:
    """Integration tests for budget profile system."""
    
    def test_profile_environment_integration(self):
        """Test profile integration with environment variables."""
        manager = BudgetProfileManager()
        
        # Test each profile can be applied
        for profile_type in UsageProfile:
            env_vars = manager.apply_profile(profile_type)
            
            # Verify all required environment variables are set
            assert "AI_DAILY_LIMIT" in env_vars
            assert "AI_MONTHLY_LIMIT" in env_vars
            assert "AI_REQUEST_LIMIT" in env_vars
            assert "AI_EMERGENCY_RESERVE" in env_vars
            assert "BUDGET_PROFILE" in env_vars
            
            # Verify values are valid numbers
            assert float(env_vars["AI_DAILY_LIMIT"]) > 0
            assert float(env_vars["AI_MONTHLY_LIMIT"]) > 0
            assert float(env_vars["AI_REQUEST_LIMIT"]) > 0
            assert float(env_vars["AI_EMERGENCY_RESERVE"]) >= 0
            
            # Verify profile name matches
            assert env_vars["BUDGET_PROFILE"] == profile_type.value


if __name__ == "__main__":
    pytest.main([__file__])