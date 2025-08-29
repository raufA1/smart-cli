"""AI Cost Optimization System - Smart model selection for budget control."""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Manual .env file loading
def load_env_file():
    """Load environment variables from .env file manually."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")


# Load .env file at module import
load_env_file()


class ModelTier(Enum):
    """Model cost tiers."""

    CHEAP = "cheap"  # $0.001-0.01 per 1K tokens
    MEDIUM = "medium"  # $0.01-0.05 per 1K tokens
    EXPENSIVE = "expensive"  # $0.05+ per 1K tokens


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # Basic operations, short responses
    MEDIUM = "medium"  # Standard development tasks
    COMPLEX = "complex"  # Architecture, complex analysis
    CRITICAL = "critical"  # High-stakes, needs best quality


@dataclass
class ModelConfig:
    """Model configuration with cost information."""

    name: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    tier: ModelTier
    strengths: List[str]
    max_tokens: int
    speed_rating: int  # 1-10, 10 is fastest


@dataclass
class CostBudget:
    """Budget configuration."""

    daily_limit: float
    per_request_limit: float
    monthly_limit: float
    emergency_reserve: float


class AICostOptimizer:
    """Smart AI model selection for cost optimization."""

    def __init__(self):
        # Model registry with real pricing
        self.models = {
            # Cheap models
            "llama-3-8b": ModelConfig(
                name="meta-llama/llama-3-8b-instruct",
                provider="openrouter",
                cost_per_1k_input=0.0007,
                cost_per_1k_output=0.0007,
                tier=ModelTier.CHEAP,
                strengths=["code_generation", "simple_analysis"],
                max_tokens=4096,
                speed_rating=9,
            ),
            "claude-haiku": ModelConfig(
                name="anthropic/claude-3-haiku-20240307",
                provider="openrouter",
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
                tier=ModelTier.CHEAP,
                strengths=["quick_analysis", "simple_tasks"],
                max_tokens=4096,
                speed_rating=10,
            ),
            # Medium models
            "llama-3-70b": ModelConfig(
                name="meta-llama/llama-3-70b-instruct",
                provider="openrouter",
                cost_per_1k_input=0.0007,
                cost_per_1k_output=0.0008,
                tier=ModelTier.MEDIUM,
                strengths=["code_analysis", "architecture", "testing"],
                max_tokens=8192,
                speed_rating=7,
            ),
            "gpt-4o-mini": ModelConfig(
                name="openai/gpt-4o-mini-2024-07-18",
                provider="openrouter",
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
                tier=ModelTier.MEDIUM,
                strengths=["general_purpose", "code_review"],
                max_tokens=4096,
                speed_rating=8,
            ),
            # Expensive models (for critical tasks)
            "claude-sonnet": ModelConfig(
                name="anthropic/claude-3.5-sonnet-20241022",
                provider="openrouter",
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                tier=ModelTier.EXPENSIVE,
                strengths=["complex_analysis", "architecture", "critical_debugging"],
                max_tokens=4096,
                speed_rating=6,
            ),
            "gpt-4-turbo": ModelConfig(
                name="openai/gpt-4-turbo-preview",
                provider="openrouter",
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                tier=ModelTier.EXPENSIVE,
                strengths=["creative_solutions", "complex_architecture"],
                max_tokens=4096,
                speed_rating=5,
            ),
        }

        # Load budget settings from environment (.env file loaded above)
        self.budget = CostBudget(
            daily_limit=float(os.getenv("AI_DAILY_LIMIT", "5.00")),
            per_request_limit=float(os.getenv("AI_REQUEST_LIMIT", "0.50")),
            monthly_limit=float(os.getenv("AI_MONTHLY_LIMIT", "100.00")),
            emergency_reserve=float(os.getenv("AI_EMERGENCY_RESERVE", "10.00")),
        )

        # Cost tracking
        self.daily_usage = 0.0
        self.monthly_usage = 0.0
        self.last_reset = datetime.now().date()

        # Agent-specific model assignments
        self.agent_model_preferences = {
            "analyzer": {
                TaskComplexity.SIMPLE: ["claude-haiku", "llama-3-8b"],
                TaskComplexity.MEDIUM: ["llama-3-70b", "gpt-4o-mini"],
                TaskComplexity.COMPLEX: ["claude-sonnet"],
                TaskComplexity.CRITICAL: ["claude-sonnet"],
            },
            "architect": {
                TaskComplexity.SIMPLE: ["llama-3-70b"],
                TaskComplexity.MEDIUM: ["llama-3-70b", "claude-sonnet"],
                TaskComplexity.COMPLEX: ["claude-sonnet"],
                TaskComplexity.CRITICAL: ["claude-sonnet", "gpt-4-turbo"],
            },
            "modifier": {
                TaskComplexity.SIMPLE: ["llama-3-8b", "claude-haiku"],
                TaskComplexity.MEDIUM: ["llama-3-70b"],
                TaskComplexity.COMPLEX: ["claude-sonnet"],
                TaskComplexity.CRITICAL: ["claude-sonnet"],
            },
            "tester": {
                TaskComplexity.SIMPLE: ["llama-3-8b"],
                TaskComplexity.MEDIUM: ["llama-3-70b", "gpt-4o-mini"],
                TaskComplexity.COMPLEX: ["llama-3-70b"],
                TaskComplexity.CRITICAL: ["claude-sonnet"],
            },
            "reviewer": {
                TaskComplexity.SIMPLE: ["gpt-4o-mini"],
                TaskComplexity.MEDIUM: ["llama-3-70b"],
                TaskComplexity.COMPLEX: ["claude-sonnet"],
                TaskComplexity.CRITICAL: ["claude-sonnet"],
            },
        }

    def assess_task_complexity(
        self, agent_name: str, task_description: str
    ) -> TaskComplexity:
        """Assess task complexity based on description and context."""
        description_lower = task_description.lower()

        # Critical task indicators
        if any(
            word in description_lower
            for word in [
                "production",
                "deploy",
                "security",
                "authentication",
                "critical",
                "bug fix",
                "performance issue",
                "database",
                "architecture",
            ]
        ):
            return TaskComplexity.CRITICAL

        # Complex task indicators
        if any(
            word in description_lower
            for word in [
                "design",
                "implement",
                "refactor",
                "optimize",
                "analyze complex",
                "multi",
                "integration",
                "system",
                "framework",
            ]
        ):
            return TaskComplexity.COMPLEX

        # Medium complexity
        if any(
            word in description_lower
            for word in ["create", "modify", "update", "test", "review", "improve"]
        ):
            return TaskComplexity.MEDIUM

        # Simple tasks
        return TaskComplexity.SIMPLE

    def select_optimal_model(
        self, agent_name: str, task_description: str, estimated_tokens: int = 2000
    ) -> Tuple[str, float]:
        """Select most cost-effective model for the task."""

        # Reset daily usage if needed
        self._reset_daily_usage_if_needed()

        # Assess task complexity
        complexity = self.assess_task_complexity(agent_name, task_description)

        # Get preferred models for this agent/complexity
        preferred_models = self.agent_model_preferences.get(
            agent_name, self.agent_model_preferences["analyzer"]  # Fallback
        ).get(complexity, ["llama-3-8b"])

        # Calculate costs for each preferred model
        model_costs = []
        for model_key in preferred_models:
            if model_key in self.models:
                model = self.models[model_key]
                # Estimate cost (assuming 30% input, 70% output ratio)
                input_tokens = int(estimated_tokens * 0.3)
                output_tokens = int(estimated_tokens * 0.7)

                cost = (input_tokens / 1000) * model.cost_per_1k_input + (
                    output_tokens / 1000
                ) * model.cost_per_1k_output

                model_costs.append((model_key, model, cost))

        # Sort by cost (cheapest first)
        model_costs.sort(key=lambda x: x[2])

        # Check budget constraints
        for model_key, model, estimated_cost in model_costs:
            if self._can_afford(estimated_cost):
                return model.name, estimated_cost

        # If we can't afford any preferred model, use cheapest available
        cheapest_model = min(
            self.models.values(),
            key=lambda m: m.cost_per_1k_input + m.cost_per_1k_output,
        )
        fallback_cost = self._calculate_cost(cheapest_model, estimated_tokens)

        if self._can_afford(fallback_cost):
            return cheapest_model.name, fallback_cost

        # Emergency: Use free/local model or fail gracefully
        raise Exception(
            f"Daily budget exceeded: ${self.daily_usage:.2f}/{self.budget.daily_limit:.2f}"
        )

    def _calculate_cost(self, model: ModelConfig, estimated_tokens: int) -> float:
        """Calculate cost for model usage."""
        input_tokens = int(estimated_tokens * 0.3)
        output_tokens = int(estimated_tokens * 0.7)

        return (input_tokens / 1000) * model.cost_per_1k_input + (
            output_tokens / 1000
        ) * model.cost_per_1k_output

    def _can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford this cost."""
        return (
            self.daily_usage + estimated_cost <= self.budget.daily_limit
            and estimated_cost <= self.budget.per_request_limit
            and self.monthly_usage + estimated_cost <= self.budget.monthly_limit
        )

    def _reset_daily_usage_if_needed(self):
        """Reset daily usage counter if new day."""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_usage = 0.0
            self.last_reset = today

    def record_usage(self, actual_cost: float):
        """Record actual API usage cost."""
        self.daily_usage += actual_cost
        self.monthly_usage += actual_cost

    def get_budget_status(self) -> Dict[str, any]:
        """Get current budget status."""
        self._reset_daily_usage_if_needed()

        return {
            "daily_usage": self.daily_usage,
            "daily_limit": self.budget.daily_limit,
            "daily_remaining": self.budget.daily_limit - self.daily_usage,
            "daily_percentage": (self.daily_usage / self.budget.daily_limit) * 100,
            "monthly_usage": self.monthly_usage,
            "monthly_limit": self.budget.monthly_limit,
            "monthly_remaining": self.budget.monthly_limit - self.monthly_usage,
            "can_continue": self.daily_usage < self.budget.daily_limit,
        }

    def suggest_cost_optimization(self, agent_usage: Dict[str, float]) -> List[str]:
        """Suggest cost optimization strategies."""
        suggestions = []

        status = self.get_budget_status()

        if status["daily_percentage"] > 80:
            suggestions.append(
                "🚨 Daily budget almost exhausted - consider using cheaper models"
            )

        if status["daily_usage"] > 2.0:
            suggestions.append(
                "💡 High usage detected - enable more aggressive caching"
            )

        # Analyze agent usage patterns
        high_cost_agents = [agent for agent, cost in agent_usage.items() if cost > 1.0]
        if high_cost_agents:
            suggestions.append(
                f"📊 High-cost agents: {', '.join(high_cost_agents)} - consider model downgrades"
            )

        if len(suggestions) == 0:
            suggestions.append("✅ Cost usage is optimal")

        return suggestions

    def create_cost_report(self) -> str:
        """Create detailed cost usage report."""
        status = self.get_budget_status()

        report = f"""
🏦 AI Cost Usage Report - {datetime.now().strftime('%Y-%m-%d')}

💰 Daily Budget:
   • Used: ${status['daily_usage']:.3f} / ${status['daily_limit']:.2f}
   • Remaining: ${status['daily_remaining']:.3f}
   • Usage: {status['daily_percentage']:.1f}%

📅 Monthly Budget: 
   • Used: ${status['monthly_usage']:.2f} / ${status['monthly_limit']:.2f}
   • Remaining: ${status['monthly_remaining']:.2f}

🤖 Model Pricing:
"""

        for name, model in self.models.items():
            report += f"   • {name}: ${model.cost_per_1k_input:.4f}→${model.cost_per_1k_output:.4f}/1K tokens\n"

        return report.strip()


# Global cost optimizer instance
_cost_optimizer = None


def get_cost_optimizer() -> AICostOptimizer:
    """Get global cost optimizer instance."""
    global _cost_optimizer
    if _cost_optimizer is None:
        _cost_optimizer = AICostOptimizer()
    return _cost_optimizer
