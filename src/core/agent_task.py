"""Standard Agent Task and Report formats."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskKind(Enum):
    """Task types for agents."""

    ANALYZE = "analyze"
    DESIGN = "design"
    MODIFY = "modify"
    TEST = "test"
    REVIEW = "review"
    DEBUG = "debug"
    LEARN = "learn"


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    """Task execution status."""

    OK = "ok"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class Decision(Enum):
    """Agent decision outcomes."""

    APPROVE = "approve"
    REVISE = "revise"
    BLOCK = "block"


@dataclass
class AgentTask:
    """Standardized input format for all agents."""

    id: str
    kind: TaskKind
    inputs: Dict[str, Any]
    context: Dict[str, Any]
    constraints: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM

    @classmethod
    def create(
        cls,
        kind: TaskKind,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> "AgentTask":
        """Create new agent task with generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            kind=kind,
            inputs=inputs or {},
            context=context or {},
            constraints=constraints or {},
            priority=priority,
        )


@dataclass
class AgentReport:
    """Standardized output format for all agents."""

    task_id: str
    status: TaskStatus
    findings: List[Dict[str, Any]]
    changes: List[Dict[str, Any]]
    decision: Optional[Decision] = None
    handoff: Optional[Dict[str, str]] = None  # {"to": "agent", "brief": "..."}
    artifacts: List[str] = None  # File paths created/modified
    metrics: Dict[str, Any] = None  # Duration, cost, resource usage
    logs: List[str] = None  # Brief log entries for UI

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.metrics is None:
            self.metrics = {}
        if self.logs is None:
            self.logs = []

        # Add timestamp
        if "timestamp" not in self.metrics:
            self.metrics["timestamp"] = datetime.now().isoformat()

    @property
    def cost(self) -> float:
        """Get task cost from metrics."""
        return self.metrics.get("cost", 0.0)

    @property
    def duration(self) -> float:
        """Get task duration from metrics."""
        return self.metrics.get("duration_seconds", 0.0)

    def add_finding(
        self,
        finding_type: str,
        description: str,
        line: Optional[int] = None,
        file_path: Optional[str] = None,
    ):
        """Add a finding to the report."""
        finding = {"type": finding_type, "description": description}
        if line:
            finding["line"] = line
        if file_path:
            finding["file_path"] = file_path
        self.findings.append(finding)

    def add_change(self, change_type: str, file_path: str, description: str):
        """Add a change to the report."""
        self.changes.append(
            {"type": change_type, "file_path": file_path, "description": description}
        )

    def add_log(self, message: str):
        """Add a log entry."""
        self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def set_cost(self, cost: float):
        """Set the cost for this task."""
        self.metrics["cost"] = cost

    def set_duration(self, seconds: float):
        """Set the duration for this task."""
        self.metrics["duration_seconds"] = seconds
