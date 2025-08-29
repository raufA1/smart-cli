"""Meta-Learning Agent - Self-improvement and performance optimization."""

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent


@dataclass
class PerformanceMetric:
    """Performance tracking data structure."""

    agent_name: str
    task_type: str
    success_rate: float
    avg_completion_time: float
    user_satisfaction: float
    timestamp: str
    details: Dict[str, Any]


@dataclass
class LearningPattern:
    """Identified learning pattern."""

    pattern_type: str
    description: str
    frequency: int
    improvement_suggestion: str
    confidence: float


class MetaLearningAgent(BaseAgent):
    """Agent that learns from system performance and improves itself."""

    def __init__(self, ai_client, session_data_path: str = ".smart_learning"):
        super().__init__("MetaLearningAgent", ai_client)
        self.session_data_path = session_data_path
        self.performance_history: List[PerformanceMetric] = []
        self.learning_patterns: List[LearningPattern] = []
        self.knowledge_base = {}

        # Create data directory
        os.makedirs(session_data_path, exist_ok=True)

        # Load existing data
        self._load_performance_history()
        self._load_learning_patterns()
        self._load_knowledge_base()

    async def analyze_system_performance(self) -> Dict[str, Any]:
        """Analyze overall system performance and identify improvement areas."""
        analysis_prompt = f"""
Analyze Smart CLI system performance based on this data:

Performance History:
{json.dumps([asdict(m) for m in self.performance_history[-10:]], indent=2)}

Learning Patterns:
{json.dumps([asdict(p) for p in self.learning_patterns], indent=2)}

Identify:
1. Performance bottlenecks
2. Agent efficiency issues  
3. User satisfaction patterns
4. Code quality trends
5. Specific improvement recommendations

Provide actionable insights in JSON format:
{{
    "bottlenecks": ["issue1", "issue2"],
    "agent_efficiency": {{"agent_name": efficiency_score}},
    "user_patterns": ["pattern1", "pattern2"],
    "quality_trends": "improving/declining/stable",
    "recommendations": ["rec1", "rec2"]
}}
"""

        try:
            response = await self.ai_client.generate_response(analysis_prompt)
            analysis = json.loads(response.content)

            # Store analysis
            self._save_analysis_result(analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}

    async def optimize_agent_prompts(self, agent_name: str, current_prompt: str) -> str:
        """Optimize agent prompts based on performance data."""

        # Get performance data for this agent
        agent_metrics = [
            m for m in self.performance_history if m.agent_name == agent_name
        ]

        optimization_prompt = f"""
You are a prompt engineering expert. Optimize this agent prompt based on performance data.

Current Prompt:
{current_prompt}

Agent: {agent_name}
Performance Data:
- Success Rate: {self._calculate_success_rate(agent_metrics)}
- Common Failures: {self._identify_failure_patterns(agent_metrics)}
- User Feedback: {self._extract_feedback_patterns(agent_metrics)}

Optimize the prompt to:
1. Address common failure modes
2. Improve success rate
3. Better handle edge cases
4. Maintain agent personality and expertise

Return only the optimized prompt, no explanation.
"""

        try:
            response = await self.ai_client.generate_response(optimization_prompt)
            optimized_prompt = response.content.strip()

            # Log optimization
            self._log_prompt_optimization(agent_name, current_prompt, optimized_prompt)

            return optimized_prompt

        except Exception as e:
            self.logger.error(f"Prompt optimization failed: {e}")
            return current_prompt

    async def learn_from_success(
        self, task_type: str, successful_implementation: Dict[str, Any]
    ):
        """Learn from successful implementations to improve future performance."""

        learning_prompt = f"""
Extract learnable patterns from this successful implementation:

Task Type: {task_type}
Implementation Details:
{json.dumps(successful_implementation, indent=2)}

Identify:
1. Key success factors
2. Reusable patterns
3. Best practices demonstrated
4. Code structures that worked well
5. Approach patterns worth replicating

Format as JSON:
{{
    "success_factors": ["factor1", "factor2"],
    "reusable_patterns": {{"pattern_name": "description"}},
    "best_practices": ["practice1", "practice2"],
    "code_patterns": {{"pattern_type": "code_example"}},
    "methodology": "description_of_successful_approach"
}}
"""

        try:
            response = await self.ai_client.generate_response(learning_prompt)
            learning_data = json.loads(response.content)

            # Update knowledge base
            self._update_knowledge_base(task_type, learning_data)

            return learning_data

        except Exception as e:
            self.logger.error(f"Success learning failed: {e}")
            return None

    async def predict_task_success(
        self, task_description: str, agent_assignment: str
    ) -> Dict[str, Any]:
        """Predict task success probability and provide optimization suggestions."""

        prediction_prompt = f"""
Based on historical performance data, predict success for this task:

Task: {task_description}
Assigned Agent: {agent_assignment}

Historical Performance:
{json.dumps(self._get_relevant_history(task_description, agent_assignment), indent=2)}

Provide prediction in JSON format:
{{
    "success_probability": 0.85,
    "confidence": 0.9,
    "risk_factors": ["factor1", "factor2"],
    "optimization_suggestions": ["suggestion1", "suggestion2"],
    "recommended_approach": "approach_description"
}}
"""

        try:
            response = await self.ai_client.generate_response(prediction_prompt)
            prediction = json.loads(response.content)

            return prediction

        except Exception as e:
            self.logger.error(f"Task prediction failed: {e}")
            return {"success_probability": 0.5, "confidence": 0.1, "error": str(e)}

    def record_performance(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        completion_time: float,
        user_feedback: float = None,
        details: Dict = None,
    ):
        """Record performance metrics for learning."""

        metric = PerformanceMetric(
            agent_name=agent_name,
            task_type=task_type,
            success_rate=1.0 if success else 0.0,
            avg_completion_time=completion_time,
            user_satisfaction=user_feedback or 0.5,
            timestamp=datetime.now().isoformat(),
            details=details or {},
        )

        self.performance_history.append(metric)
        self._save_performance_history()

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get current learning insights and recommendations."""
        return {
            "total_sessions": len(self.performance_history),
            "recent_trends": self._analyze_recent_trends(),
            "top_patterns": self.learning_patterns[:5],
            "knowledge_areas": list(self.knowledge_base.keys()),
            "improvement_areas": self._identify_improvement_areas(),
        }

    # Private helper methods
    def _load_performance_history(self):
        """Load performance history from storage."""
        try:
            history_path = os.path.join(
                self.session_data_path, "performance_history.json"
            )
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    data = json.load(f)
                    self.performance_history = [
                        PerformanceMetric(**item) for item in data
                    ]
        except Exception as e:
            self.logger.warning(f"Could not load performance history: {e}")

    def _save_performance_history(self):
        """Save performance history to storage."""
        try:
            history_path = os.path.join(
                self.session_data_path, "performance_history.json"
            )
            with open(history_path, "w") as f:
                json.dump([asdict(m) for m in self.performance_history], f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save performance history: {e}")

    def _load_learning_patterns(self):
        """Load learning patterns from storage."""
        try:
            patterns_path = os.path.join(
                self.session_data_path, "learning_patterns.json"
            )
            if os.path.exists(patterns_path):
                with open(patterns_path, "r") as f:
                    data = json.load(f)
                    self.learning_patterns = [LearningPattern(**item) for item in data]
        except Exception as e:
            self.logger.warning(f"Could not load learning patterns: {e}")

    def _load_knowledge_base(self):
        """Load knowledge base from storage."""
        try:
            kb_path = os.path.join(self.session_data_path, "knowledge_base.json")
            if os.path.exists(kb_path):
                with open(kb_path, "r") as f:
                    self.knowledge_base = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load knowledge base: {e}")

    def _calculate_success_rate(self, metrics: List[PerformanceMetric]) -> float:
        """Calculate success rate from metrics."""
        if not metrics:
            return 0.5
        return sum(m.success_rate for m in metrics) / len(metrics)

    def _identify_failure_patterns(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Identify common failure patterns."""
        failures = [m for m in metrics if m.success_rate < 0.5]
        # Extract common failure reasons from details
        patterns = []
        for failure in failures:
            if "error" in failure.details:
                patterns.append(failure.details["error"])
        return list(set(patterns))

    def _extract_feedback_patterns(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Extract patterns from user feedback."""
        feedback_patterns = []
        for metric in metrics:
            if "user_feedback" in metric.details:
                feedback_patterns.append(metric.details["user_feedback"])
        return feedback_patterns

    def _get_relevant_history(
        self, task_description: str, agent_name: str
    ) -> List[Dict]:
        """Get relevant historical performance for prediction."""
        relevant = []
        for metric in self.performance_history:
            if metric.agent_name == agent_name or any(
                keyword in task_description.lower()
                for keyword in metric.task_type.lower().split()
            ):
                relevant.append(asdict(metric))
        return relevant[-5:]  # Last 5 relevant entries

    def _analyze_recent_trends(self) -> Dict[str, Any]:
        """Analyze recent performance trends."""
        if len(self.performance_history) < 5:
            return {"trend": "insufficient_data"}

        recent = self.performance_history[-10:]
        older = (
            self.performance_history[-20:-10]
            if len(self.performance_history) >= 20
            else []
        )

        recent_success = sum(m.success_rate for m in recent) / len(recent)
        older_success = (
            sum(m.success_rate for m in older) / len(older) if older else recent_success
        )

        return {
            "trend": "improving" if recent_success > older_success else "declining",
            "recent_success_rate": recent_success,
            "change": recent_success - older_success,
        }

    def _identify_improvement_areas(self) -> List[str]:
        """Identify areas that need improvement."""
        # Group by agent and task type
        agent_performance = {}
        for metric in self.performance_history:
            key = metric.agent_name
            if key not in agent_performance:
                agent_performance[key] = []
            agent_performance[key].append(metric.success_rate)

        improvement_areas = []
        for agent, rates in agent_performance.items():
            avg_rate = sum(rates) / len(rates)
            if avg_rate < 0.7:  # Below 70% success rate
                improvement_areas.append(f"{agent} (success rate: {avg_rate:.2f})")

        return improvement_areas

    def _save_analysis_result(self, analysis: Dict[str, Any]):
        """Save analysis results."""
        try:
            analysis_path = os.path.join(self.session_data_path, "latest_analysis.json")
            with open(analysis_path, "w") as f:
                json.dump(
                    {"timestamp": datetime.now().isoformat(), "analysis": analysis},
                    f,
                    indent=2,
                )
        except Exception as e:
            self.logger.error(f"Could not save analysis: {e}")

    def _log_prompt_optimization(
        self, agent_name: str, old_prompt: str, new_prompt: str
    ):
        """Log prompt optimization."""
        try:
            opt_log_path = os.path.join(
                self.session_data_path, "prompt_optimizations.json"
            )

            optimization = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "old_prompt": old_prompt[:200] + "...",
                "new_prompt": new_prompt[:200] + "...",
                "optimization_id": len(self.performance_history),
            }

            if os.path.exists(opt_log_path):
                with open(opt_log_path, "r") as f:
                    optimizations = json.load(f)
            else:
                optimizations = []

            optimizations.append(optimization)

            with open(opt_log_path, "w") as f:
                json.dump(optimizations, f, indent=2)

        except Exception as e:
            self.logger.error(f"Could not log prompt optimization: {e}")

    def _update_knowledge_base(self, task_type: str, learning_data: Dict[str, Any]):
        """Update knowledge base with new learning."""
        if task_type not in self.knowledge_base:
            self.knowledge_base[task_type] = {
                "best_practices": [],
                "success_patterns": {},
                "code_templates": {},
                "methodologies": [],
            }

        kb_entry = self.knowledge_base[task_type]

        # Update with new learning
        if "best_practices" in learning_data:
            kb_entry["best_practices"].extend(learning_data["best_practices"])
            kb_entry["best_practices"] = list(
                set(kb_entry["best_practices"])
            )  # Deduplicate

        if "reusable_patterns" in learning_data:
            kb_entry["success_patterns"].update(learning_data["reusable_patterns"])

        if "code_patterns" in learning_data:
            kb_entry["code_templates"].update(learning_data["code_patterns"])

        if "methodology" in learning_data:
            kb_entry["methodologies"].append(learning_data["methodology"])

        # Save updated knowledge base
        try:
            kb_path = os.path.join(self.session_data_path, "knowledge_base.json")
            with open(kb_path, "w") as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save knowledge base: {e}")
