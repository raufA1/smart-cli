"""Smart Task Classification System - Determines optimal agent pipeline based on task complexity."""

import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TaskComplexity(Enum):
    """Task complexity levels for pipeline optimization."""

    MICRO = "micro"  # ≤2 files, simple changes
    MEDIUM = "medium"  # 3-10 files, standard features
    COMPLEX = "complex"  # >10 files, multi-module
    CRITICAL = "critical"  # High-risk: security, auth, DB


class TaskRisk(Enum):
    """Task risk levels for model selection."""

    LOW = "low"  # UI, docs, text changes
    MEDIUM = "medium"  # Standard features, improvements
    HIGH = "high"  # Architecture, complex refactoring
    CRITICAL = "critical"  # Security, auth, database, payments


class TaskClassifier:
    """Classifies tasks to determine optimal agent pipeline and model selection."""

    def __init__(self):
        # Critical risk patterns (security, auth, database)
        self.critical_patterns = [
            "auth",
            "authentication",
            "login",
            "password",
            "security",
            "database",
            "db",
            "sql",
            "migration",
            "payment",
            "crypto",
            "secret",
            "token",
            "jwt",
            "oauth",
            "permission",
            "role",
        ]

        # High risk patterns (architecture, complex changes)
        self.high_risk_patterns = [
            "architecture",
            "refactor",
            "redesign",
            "system design",
            "multi-module",
            "framework",
            "integration",
            "api design",
            "performance",
            "optimize",
            "concurrency",
            "async",
        ]

        # Medium risk patterns (standard features)
        self.medium_risk_patterns = [
            "feature",
            "implement",
            "create",
            "build",
            "develop",
            "improve",
            "enhance",
            "update",
            "modify",
            "fix bug",
            "add functionality",
            "extend",
        ]

        # Override patterns for low risk (even if they contain medium risk words)
        self.low_risk_override_patterns = [
            "fix small",
            "fix typo",
            "fix text",
            "small fix",
            "minor fix",
            "quick fix",
            "simple fix",
        ]

        # Low risk patterns (simple changes)
        self.low_risk_patterns = [
            "text",
            "docs",
            "documentation",
            "readme",
            "comment",
            "ui",
            "style",
            "css",
            "html",
            "formatting",
            "lint",
            "rename",
            "move file",
            "delete",
        ]

        # File extensions by risk
        self.high_risk_files = {".sql", ".migration", ".env", ".config"}
        self.medium_risk_files = {".py", ".js", ".ts", ".java", ".go", ".rs"}
        self.low_risk_files = {".md", ".txt", ".html", ".css", ".json", ".yaml"}

    def classify_task(
        self, user_request: str, context: Optional[Dict] = None
    ) -> Tuple[TaskComplexity, TaskRisk]:
        """
        Classify task complexity and risk level.

        Args:
            user_request: User's request text
            context: Optional context (file_count, file_paths, etc.)

        Returns:
            Tuple of (TaskComplexity, TaskRisk)
        """
        request_lower = user_request.lower()

        # Determine risk level first
        risk = self._classify_risk(request_lower, context)

        # Determine complexity based on risk and context
        complexity = self._classify_complexity(request_lower, context, risk)

        return complexity, risk

    def _classify_risk(self, request_lower: str, context: Optional[Dict]) -> TaskRisk:
        """Classify risk level based on patterns and context."""

        # Check for low-risk override patterns first
        if any(pattern in request_lower for pattern in self.low_risk_override_patterns):
            return TaskRisk.LOW

        # Check for critical patterns
        if any(pattern in request_lower for pattern in self.critical_patterns):
            return TaskRisk.CRITICAL

        # Check for high-risk patterns
        if any(pattern in request_lower for pattern in self.high_risk_patterns):
            return TaskRisk.HIGH

        # Check file context if available
        if context and "file_paths" in context:
            file_paths = context["file_paths"]
            for file_path in file_paths:
                file_ext = Path(file_path).suffix.lower()
                if file_ext in self.high_risk_files:
                    return TaskRisk.CRITICAL

        # Check for medium risk patterns
        if any(pattern in request_lower for pattern in self.medium_risk_patterns):
            return TaskRisk.MEDIUM

        # Check for low risk patterns or default to medium
        if any(pattern in request_lower for pattern in self.low_risk_patterns):
            return TaskRisk.LOW

        return TaskRisk.MEDIUM  # Default fallback

    def _classify_complexity(
        self, request_lower: str, context: Optional[Dict], risk: TaskRisk
    ) -> TaskComplexity:
        """Classify task complexity based on scope and risk."""

        # Critical risk always gets full pipeline
        if risk == TaskRisk.CRITICAL:
            return TaskComplexity.CRITICAL

        # Check context for file count
        file_count = 0
        if context:
            file_count = context.get("file_count", 0)
            file_paths = context.get("file_paths", [])
            file_count = max(file_count, len(file_paths))

        # Estimate file count from request if not provided
        if file_count == 0:
            file_count = self._estimate_file_count(request_lower)

        # Complexity classification
        if file_count <= 2 and risk == TaskRisk.LOW:
            return TaskComplexity.MICRO
        elif file_count <= 2 and risk in [TaskRisk.LOW, TaskRisk.MEDIUM]:
            return TaskComplexity.MEDIUM
        elif file_count <= 10:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.COMPLEX

    def _estimate_file_count(self, request_lower: str) -> int:
        """Estimate number of files that will be affected."""

        # Multi-file indicators
        if any(
            word in request_lower
            for word in [
                "project",
                "application",
                "system",
                "multi",
                "entire",
                "full",
                "complete",
                "all files",
                "whole",
            ]
        ):
            return 15  # Complex

        # Medium scope indicators
        if any(
            word in request_lower
            for word in [
                "module",
                "component",
                "service",
                "package",
                "feature",
                "class",
                "interface",
                "api",
            ]
        ):
            return 5  # Medium

        # Simple scope indicators
        if any(
            word in request_lower
            for word in [
                "function",
                "method",
                "variable",
                "fix",
                "small",
                "simple",
                "quick",
                "minor",
                "typo",
                "text",
                "comment",
            ]
        ):
            return 1  # Micro

        return 3  # Default medium

    def get_recommended_pipeline(
        self, complexity: TaskComplexity, risk: TaskRisk
    ) -> List[str]:
        """Get recommended agent pipeline based on classification."""

        if complexity == TaskComplexity.MICRO:
            # Skip architect for simple changes
            return ["modifier"]

        elif complexity == TaskComplexity.MEDIUM:
            # Standard pipeline without full analysis
            if risk in [TaskRisk.LOW, TaskRisk.MEDIUM]:
                return ["architect", "modifier", "tester"]
            else:
                return ["analyzer", "architect", "modifier", "tester"]

        elif complexity == TaskComplexity.COMPLEX:
            # Full pipeline with analysis
            return ["analyzer", "architect", "modifier", "tester", "reviewer"]

        elif complexity == TaskComplexity.CRITICAL:
            # Full pipeline with extra scrutiny
            return ["analyzer", "architect", "modifier", "tester", "reviewer"]

        return ["modifier"]  # Fallback

    def get_recommended_models(
        self, complexity: TaskComplexity, risk: TaskRisk
    ) -> Dict[str, str]:
        """Get recommended models for each agent based on classification."""

        if risk == TaskRisk.CRITICAL:
            # Use expensive models for critical tasks
            return {
                "analyzer": "claude-sonnet",
                "architect": "claude-sonnet",
                "modifier": "claude-sonnet",
                "tester": "llama-3-70b",
                "reviewer": "claude-sonnet",
            }

        elif risk == TaskRisk.HIGH:
            # Mix of medium and expensive models
            return {
                "analyzer": "llama-3-70b",
                "architect": "claude-sonnet",
                "modifier": "llama-3-70b",
                "tester": "llama-3-70b",
                "reviewer": "claude-sonnet",
            }

        elif risk == TaskRisk.MEDIUM:
            # Mostly medium models
            return {
                "analyzer": "llama-3-70b",
                "architect": "llama-3-70b",
                "modifier": "gpt-4o-mini",
                "tester": "llama-3-8b",
                "reviewer": "gpt-4o-mini",
            }

        else:  # TaskRisk.LOW
            # Cheap models for simple tasks
            return {
                "analyzer": "llama-3-8b",
                "architect": "gpt-4o-mini",
                "modifier": "llama-3-8b",
                "tester": "llama-3-8b",
                "reviewer": "claude-haiku",
            }

    def create_classification_report(
        self, user_request: str, context: Optional[Dict] = None
    ) -> Dict:
        """Create detailed classification report for debugging."""
        complexity, risk = self.classify_task(user_request, context)
        pipeline = self.get_recommended_pipeline(complexity, risk)
        models = self.get_recommended_models(complexity, risk)

        return {
            "user_request": user_request,
            "complexity": complexity.value,
            "risk": risk.value,
            "recommended_pipeline": pipeline,
            "recommended_models": models,
            "estimated_file_count": (
                context.get("file_count", 0)
                if context
                else self._estimate_file_count(user_request.lower())
            ),
            "reasoning": {
                "complexity_factors": self._get_complexity_factors(
                    user_request.lower(), context
                ),
                "risk_factors": self._get_risk_factors(user_request.lower(), context),
            },
        }

    def _get_complexity_factors(
        self, request_lower: str, context: Optional[Dict]
    ) -> List[str]:
        """Get factors that influenced complexity classification."""
        factors = []

        if any(word in request_lower for word in ["project", "system", "multi"]):
            factors.append("Multi-file scope detected")
        if context and context.get("file_count", 0) > 10:
            factors.append(f"High file count: {context['file_count']}")
        if any(word in request_lower for word in ["simple", "quick", "minor"]):
            factors.append("Simple scope indicators")

        return factors

    def _get_risk_factors(
        self, request_lower: str, context: Optional[Dict]
    ) -> List[str]:
        """Get factors that influenced risk classification."""
        factors = []

        for pattern in self.critical_patterns:
            if pattern in request_lower:
                factors.append(f"Critical pattern: {pattern}")

        for pattern in self.high_risk_patterns:
            if pattern in request_lower:
                factors.append(f"High risk pattern: {pattern}")

        if context and "file_paths" in context:
            for file_path in context["file_paths"]:
                if Path(file_path).suffix.lower() in self.high_risk_files:
                    factors.append(f"High risk file: {file_path}")

        return factors


# Global instance
_task_classifier = None


def get_task_classifier() -> TaskClassifier:
    """Get global task classifier instance."""
    global _task_classifier
    if _task_classifier is None:
        _task_classifier = TaskClassifier()
    return _task_classifier
