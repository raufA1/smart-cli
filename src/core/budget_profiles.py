"""Budget Profile Management - Predefined budget configurations for different use cases."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class UsageProfile(Enum):
    """Different usage profiles with appropriate budget settings."""

    STUDENT = "student"  # Learning, small projects
    DEVELOPER = "developer"  # Regular development work
    FREELANCER = "freelancer"  # Client projects, moderate usage
    STARTUP = "startup"  # Early stage company, cost-conscious
    ENTERPRISE = "enterprise"  # Large organization, high volume
    UNLIMITED = "unlimited"  # No budget constraints


@dataclass
class BudgetProfile:
    """Budget configuration profile."""

    name: str
    description: str
    daily_limit: float
    monthly_limit: float
    per_request_limit: float
    emergency_reserve: float
    recommended_models: Dict[str, str]  # agent -> preferred_model


class BudgetProfileManager:
    """Manages different budget profiles for various use cases."""

    def __init__(self):
        self.profiles = {
            UsageProfile.STUDENT: BudgetProfile(
                name="Student",
                description="Perfect for learning and small personal projects",
                daily_limit=2.00,
                monthly_limit=40.00,
                per_request_limit=0.25,
                emergency_reserve=5.00,
                recommended_models={
                    "analyzer": "claude-haiku",
                    "modifier": "llama-3-8b",
                    "architect": "llama-3-70b",
                    "tester": "llama-3-8b",
                    "reviewer": "gpt-4o-mini",
                },
            ),
            UsageProfile.DEVELOPER: BudgetProfile(
                name="Developer",
                description="Individual developer working on regular projects",
                daily_limit=8.00,
                monthly_limit=180.00,
                per_request_limit=1.00,
                emergency_reserve=15.00,
                recommended_models={
                    "analyzer": "llama-3-70b",
                    "modifier": "llama-3-70b",
                    "architect": "claude-sonnet",
                    "tester": "llama-3-70b",
                    "reviewer": "claude-sonnet",
                },
            ),
            UsageProfile.FREELANCER: BudgetProfile(
                name="Freelancer",
                description="Freelancer handling multiple client projects",
                daily_limit=15.00,
                monthly_limit=350.00,
                per_request_limit=2.00,
                emergency_reserve=25.00,
                recommended_models={
                    "analyzer": "claude-sonnet",
                    "modifier": "claude-sonnet",
                    "architect": "claude-sonnet",
                    "tester": "llama-3-70b",
                    "reviewer": "claude-sonnet",
                },
            ),
            UsageProfile.STARTUP: BudgetProfile(
                name="Startup",
                description="Early-stage startup balancing quality and cost",
                daily_limit=25.00,
                monthly_limit=600.00,
                per_request_limit=3.00,
                emergency_reserve=50.00,
                recommended_models={
                    "analyzer": "claude-sonnet",
                    "modifier": "claude-sonnet",
                    "architect": "claude-sonnet",
                    "tester": "llama-3-70b",
                    "reviewer": "claude-sonnet",
                },
            ),
            UsageProfile.ENTERPRISE: BudgetProfile(
                name="Enterprise",
                description="Large organization with high-volume usage",
                daily_limit=100.00,
                monthly_limit=2500.00,
                per_request_limit=10.00,
                emergency_reserve=200.00,
                recommended_models={
                    "analyzer": "claude-sonnet",
                    "modifier": "claude-sonnet",
                    "architect": "gpt-4-turbo",  # Best quality for critical decisions
                    "tester": "claude-sonnet",
                    "reviewer": "claude-sonnet",
                },
            ),
            UsageProfile.UNLIMITED: BudgetProfile(
                name="Unlimited",
                description="No budget constraints - use best models always",
                daily_limit=1000.00,
                monthly_limit=25000.00,
                per_request_limit=50.00,
                emergency_reserve=500.00,
                recommended_models={
                    "analyzer": "gpt-4-turbo",
                    "modifier": "claude-sonnet",
                    "architect": "gpt-4-turbo",
                    "tester": "claude-sonnet",
                    "reviewer": "gpt-4-turbo",
                },
            ),
        }

    def get_profile(self, profile_type: UsageProfile) -> BudgetProfile:
        """Get budget profile by type."""
        return self.profiles[profile_type]

    def list_profiles(self) -> Dict[UsageProfile, BudgetProfile]:
        """Get all available profiles."""
        return self.profiles

    def get_profile_by_name(self, name: str) -> BudgetProfile:
        """Get profile by name (case insensitive)."""
        name_lower = name.lower()
        for profile_type, profile in self.profiles.items():
            if profile.name.lower() == name_lower or profile_type.value == name_lower:
                return profile
        raise ValueError(f"Profile '{name}' not found")

    def recommend_profile(
        self, daily_usage_estimate: float, team_size: int = 1
    ) -> UsageProfile:
        """Recommend a profile based on usage patterns."""
        total_daily_estimate = daily_usage_estimate * team_size

        if total_daily_estimate <= 2.0:
            return UsageProfile.STUDENT
        elif total_daily_estimate <= 8.0:
            return UsageProfile.DEVELOPER
        elif total_daily_estimate <= 15.0:
            return UsageProfile.FREELANCER
        elif total_daily_estimate <= 25.0:
            return UsageProfile.STARTUP
        elif total_daily_estimate <= 100.0:
            return UsageProfile.ENTERPRISE
        else:
            return UsageProfile.UNLIMITED

    def apply_profile(self, profile_type: UsageProfile) -> Dict[str, Any]:
        """Get environment variables for a profile."""
        profile = self.get_profile(profile_type)

        return {
            "AI_DAILY_LIMIT": str(profile.daily_limit),
            "AI_MONTHLY_LIMIT": str(profile.monthly_limit),
            "AI_REQUEST_LIMIT": str(profile.per_request_limit),
            "AI_EMERGENCY_RESERVE": str(profile.emergency_reserve),
            "BUDGET_PROFILE": profile_type.value,
        }

    def get_cost_comparison(self) -> Dict[str, Dict[str, float]]:
        """Get cost comparison between profiles."""
        comparison = {}

        for profile_type, profile in self.profiles.items():
            comparison[profile.name] = {
                "daily_limit": profile.daily_limit,
                "monthly_limit": profile.monthly_limit,
                "cost_per_1k_requests_estimate": profile.per_request_limit * 1000,
                "annual_cost_estimate": profile.monthly_limit * 12,
            }

        return comparison


# Global profile manager
_profile_manager = None


def get_profile_manager() -> BudgetProfileManager:
    """Get global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = BudgetProfileManager()
    return _profile_manager
