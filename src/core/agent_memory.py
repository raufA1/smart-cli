"""Agent Memory and Learning System for Smart CLI."""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskOutcome(Enum):
    """Task execution outcomes for learning."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


@dataclass
class AgentExperience:
    """Single agent experience for learning."""

    agent_name: str
    task_type: str
    task_description: str
    context: Dict[str, Any]
    outcome: TaskOutcome
    execution_time: float
    success_metrics: Dict[str, Any]
    errors: List[str]
    created_files: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["outcome"] = self.outcome.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentExperience":
        """Create from dictionary."""
        data["outcome"] = TaskOutcome(data["outcome"])
        return cls(**data)


@dataclass
class AgentPattern:
    """Learned pattern from agent experiences."""

    pattern_id: str
    agent_name: str
    task_pattern: str
    success_rate: float
    avg_execution_time: float
    common_context: Dict[str, Any]
    recommended_approach: Dict[str, Any]
    confidence_score: float
    experience_count: int
    last_updated: float


class AgentMemorySystem:
    """Intelligent memory and learning system for agents."""

    def __init__(self, memory_dir: str = None):
        self.memory_dir = Path(memory_dir or "cache/agent_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.experiences_file = self.memory_dir / "experiences.jsonl"
        self.patterns_file = self.memory_dir / "patterns.json"

        # In-memory caches
        self.recent_experiences: List[AgentExperience] = []
        self.learned_patterns: Dict[str, AgentPattern] = {}

        # Learning parameters
        self.max_recent_experiences = 1000
        self.pattern_min_samples = 3
        self.pattern_confidence_threshold = 0.7

        # Load existing data
        self._load_memory()

    def _load_memory(self):
        """Load existing memory data."""
        # Load recent experiences
        if self.experiences_file.exists():
            try:
                with open(self.experiences_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Load last N experiences
                    for line in lines[-self.max_recent_experiences :]:
                        try:
                            data = json.loads(line.strip())
                            experience = AgentExperience.from_dict(data)
                            self.recent_experiences.append(experience)
                        except Exception:
                            continue
            except Exception:
                pass

        # Load learned patterns
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, "r", encoding="utf-8") as f:
                    patterns_data = json.load(f)
                    for pattern_data in patterns_data:
                        pattern = AgentPattern(**pattern_data)
                        self.learned_patterns[pattern.pattern_id] = pattern
            except Exception:
                pass

    def _save_experience(self, experience: AgentExperience):
        """Save single experience to file."""
        try:
            with open(self.experiences_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(experience.to_dict()) + "\n")
        except Exception:
            pass

    def _save_patterns(self):
        """Save learned patterns to file."""
        try:
            patterns_data = [
                asdict(pattern) for pattern in self.learned_patterns.values()
            ]
            with open(self.patterns_file, "w", encoding="utf-8") as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def record_agent_experience(
        self,
        agent_name: str,
        task_type: str,
        task_description: str,
        context: Dict[str, Any],
        outcome: TaskOutcome,
        execution_time: float,
        success_metrics: Dict[str, Any] = None,
        errors: List[str] = None,
        created_files: List[str] = None,
    ):
        """Record agent experience for learning."""
        experience = AgentExperience(
            agent_name=agent_name,
            task_type=task_type,
            task_description=task_description,
            context=context or {},
            outcome=outcome,
            execution_time=execution_time,
            success_metrics=success_metrics or {},
            errors=errors or [],
            created_files=created_files or [],
            timestamp=time.time(),
        )

        # Add to recent experiences
        self.recent_experiences.append(experience)

        # Keep only recent experiences in memory
        if len(self.recent_experiences) > self.max_recent_experiences:
            self.recent_experiences = self.recent_experiences[
                -self.max_recent_experiences :
            ]

        # Save to file
        self._save_experience(experience)

        # Trigger learning
        self._update_patterns(experience)

    def _update_patterns(self, new_experience: AgentExperience):
        """Update learned patterns based on new experience."""
        pattern_key = self._generate_pattern_key(
            new_experience.agent_name, new_experience.task_type, new_experience.context
        )

        # Find similar experiences
        similar_experiences = self._find_similar_experiences(new_experience)

        if len(similar_experiences) >= self.pattern_min_samples:
            # Create or update pattern
            pattern = self._create_pattern_from_experiences(
                pattern_key, similar_experiences
            )
            if pattern.confidence_score >= self.pattern_confidence_threshold:
                self.learned_patterns[pattern_key] = pattern
                self._save_patterns()

    def _generate_pattern_key(
        self, agent_name: str, task_type: str, context: Dict[str, Any]
    ) -> str:
        """Generate unique pattern key."""
        context_signature = self._create_context_signature(context)
        key_data = f"{agent_name}:{task_type}:{context_signature}"
        return hashlib.md5(key_data.encode()).hexdigest()[:12]

    def _create_context_signature(self, context: Dict[str, Any]) -> str:
        """Create context signature for pattern matching."""
        # Extract key context features
        signature_features = []

        if "project_type" in context:
            signature_features.append(f"proj:{context['project_type']}")

        if "complexity_level" in context:
            signature_features.append(f"comp:{context['complexity_level']}")

        if "file_count" in context:
            file_count = context["file_count"]
            if file_count == 1:
                signature_features.append("single_file")
            elif file_count < 5:
                signature_features.append("small_project")
            elif file_count < 20:
                signature_features.append("medium_project")
            else:
                signature_features.append("large_project")

        if "technologies" in context:
            techs = context["technologies"]
            if isinstance(techs, list):
                signature_features.extend(
                    [f"tech:{tech.lower()}" for tech in techs[:3]]
                )

        return "|".join(sorted(signature_features))

    def _find_similar_experiences(
        self, target_experience: AgentExperience
    ) -> List[AgentExperience]:
        """Find similar experiences for pattern learning."""
        similar = []
        target_signature = self._create_context_signature(target_experience.context)

        for exp in self.recent_experiences:
            if (
                exp.agent_name == target_experience.agent_name
                and exp.task_type == target_experience.task_type
            ):

                exp_signature = self._create_context_signature(exp.context)
                similarity = self._calculate_similarity(target_signature, exp_signature)

                if similarity > 0.6:  # 60% similarity threshold
                    similar.append(exp)

        return similar

    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between context signatures."""
        if not sig1 or not sig2:
            return 0.0

        features1 = set(sig1.split("|"))
        features2 = set(sig2.split("|"))

        if not features1 and not features2:
            return 1.0

        intersection = len(features1.intersection(features2))
        union = len(features1.union(features2))

        return intersection / union if union > 0 else 0.0

    def _create_pattern_from_experiences(
        self, pattern_key: str, experiences: List[AgentExperience]
    ) -> AgentPattern:
        """Create learned pattern from similar experiences."""
        if not experiences:
            raise ValueError("Cannot create pattern from empty experiences")

        # Calculate pattern statistics
        successes = [exp for exp in experiences if exp.outcome == TaskOutcome.SUCCESS]
        success_rate = len(successes) / len(experiences)

        avg_execution_time = sum(exp.execution_time for exp in experiences) / len(
            experiences
        )

        # Extract common context features
        common_context = self._extract_common_context(experiences)

        # Create recommended approach from successful experiences
        recommended_approach = self._create_recommended_approach(successes)

        # Calculate confidence based on sample size and success rate
        confidence_score = min(1.0, (len(experiences) / 10) * success_rate)

        return AgentPattern(
            pattern_id=pattern_key,
            agent_name=experiences[0].agent_name,
            task_pattern=experiences[0].task_type,
            success_rate=success_rate,
            avg_execution_time=avg_execution_time,
            common_context=common_context,
            recommended_approach=recommended_approach,
            confidence_score=confidence_score,
            experience_count=len(experiences),
            last_updated=time.time(),
        )

    def _extract_common_context(
        self, experiences: List[AgentExperience]
    ) -> Dict[str, Any]:
        """Extract common context features from experiences."""
        if not experiences:
            return {}

        # Find features that appear in most experiences
        feature_counts = {}
        total_experiences = len(experiences)

        for exp in experiences:
            for key, value in exp.context.items():
                if key not in feature_counts:
                    feature_counts[key] = {}

                value_str = str(value)
                feature_counts[key][value_str] = (
                    feature_counts[key].get(value_str, 0) + 1
                )

        # Extract features that appear in >50% of experiences
        common_context = {}
        for key, value_counts in feature_counts.items():
            for value, count in value_counts.items():
                if count / total_experiences > 0.5:
                    common_context[key] = value
                    break

        return common_context

    def _create_recommended_approach(
        self, successful_experiences: List[AgentExperience]
    ) -> Dict[str, Any]:
        """Create recommended approach from successful experiences."""
        if not successful_experiences:
            return {}

        # Analyze successful patterns
        recommendations = {
            "avg_success_time": sum(
                exp.execution_time for exp in successful_experiences
            )
            / len(successful_experiences),
            "common_success_factors": [],
            "file_creation_patterns": [],
            "avoid_patterns": [],
        }

        # Extract common success factors
        if successful_experiences:
            # Most common file types created
            file_extensions = []
            for exp in successful_experiences:
                for file in exp.created_files:
                    if "." in file:
                        ext = file.split(".")[-1]
                        file_extensions.append(ext)

            if file_extensions:
                from collections import Counter

                common_extensions = Counter(file_extensions).most_common(3)
                recommendations["file_creation_patterns"] = [
                    ext for ext, count in common_extensions
                ]

        return recommendations

    def get_recommendation(
        self, agent_name: str, task_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get intelligent recommendation for agent task."""
        pattern_key = self._generate_pattern_key(agent_name, task_type, context)

        # Check for exact pattern match
        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            return {
                "confidence": pattern.confidence_score,
                "expected_time": pattern.avg_execution_time,
                "success_probability": pattern.success_rate,
                "recommended_approach": pattern.recommended_approach,
                "based_on_experiences": pattern.experience_count,
            }

        # Find similar patterns
        best_match = None
        best_similarity = 0.0

        target_signature = self._create_context_signature(context)

        for pattern in self.learned_patterns.values():
            if pattern.agent_name == agent_name and pattern.task_pattern == task_type:
                pattern_signature = self._create_context_signature(
                    pattern.common_context
                )
                similarity = self._calculate_similarity(
                    target_signature, pattern_signature
                )

                if similarity > best_similarity and similarity > 0.5:
                    best_similarity = similarity
                    best_match = pattern

        if best_match:
            return {
                "confidence": best_match.confidence_score * best_similarity,
                "expected_time": best_match.avg_execution_time,
                "success_probability": best_match.success_rate,
                "recommended_approach": best_match.recommended_approach,
                "based_on_experiences": best_match.experience_count,
                "similarity": best_similarity,
            }

        return None

    def get_agent_performance_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get performance statistics for specific agent."""
        agent_experiences = [
            exp for exp in self.recent_experiences if exp.agent_name == agent_name
        ]

        if not agent_experiences:
            return {"message": "No experience data available"}

        total_tasks = len(agent_experiences)
        successful_tasks = len(
            [exp for exp in agent_experiences if exp.outcome == TaskOutcome.SUCCESS]
        )

        avg_execution_time = (
            sum(exp.execution_time for exp in agent_experiences) / total_tasks
        )

        # Task type breakdown
        task_types = {}
        for exp in agent_experiences:
            task_types[exp.task_type] = task_types.get(exp.task_type, 0) + 1

        return {
            "total_tasks": total_tasks,
            "success_rate": successful_tasks / total_tasks,
            "avg_execution_time": avg_execution_time,
            "task_type_distribution": task_types,
            "learned_patterns": len(
                [
                    p
                    for p in self.learned_patterns.values()
                    if p.agent_name == agent_name
                ]
            ),
        }

    def get_system_learning_stats(self) -> Dict[str, Any]:
        """Get overall system learning statistics."""
        return {
            "total_experiences": len(self.recent_experiences),
            "learned_patterns": len(self.learned_patterns),
            "agents_with_memory": len(
                set(exp.agent_name for exp in self.recent_experiences)
            ),
            "avg_pattern_confidence": (
                sum(p.confidence_score for p in self.learned_patterns.values())
                / len(self.learned_patterns)
                if self.learned_patterns
                else 0
            ),
            "memory_size_mb": (
                (
                    self.experiences_file.stat().st_size
                    + self.patterns_file.stat().st_size
                )
                / (1024 * 1024)
                if self.experiences_file.exists() and self.patterns_file.exists()
                else 0
            ),
        }


# Global memory system instance
_global_memory = None


def get_agent_memory() -> AgentMemorySystem:
    """Get global agent memory system."""
    global _global_memory
    if _global_memory is None:
        _global_memory = AgentMemorySystem()
    return _global_memory
