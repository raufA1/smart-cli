"""Base Agent class for Smart CLI agents."""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live

try:
    from ..core.agent_task import AgentReport, AgentTask, TaskStatus
except ImportError:
    from core.agent_task import AgentReport, AgentTask, TaskStatus

console = Console()


@dataclass
class AgentReport:
    """Structured result from agent task execution."""

    success: bool
    agent_name: str
    task_description: str
    execution_time: float
    created_files: List[str]
    modified_files: List[str]
    errors: List[str]
    warnings: List[str]
    output_data: Dict[str, Any]
    next_recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class BaseAgent(ABC):
    """Base class for all Smart CLI agents."""

    def __init__(self, ai_client=None, config_manager=None):
        self.ai_client = ai_client
        self.config_manager = config_manager
        self.agent_name = "Base Agent"
        self.agent_emoji = "🤖"
        self.current_task_start = None
        
        # Initialize AI client if not provided but config manager is available
        if not self.ai_client and self.config_manager:
            from ..utils.simple_ai_client import SimpleOpenRouterClient
            self.ai_client = SimpleOpenRouterClient(self.config_manager)

        # Memory and learning system
        self.memory_enabled = True
        self.memory_system = None
        self._initialize_memory()

    @abstractmethod
    async def execute(self, target: str, description: str) -> AgentReport:
        """Execute the agent's task and return structured result."""
        pass

    async def execute_task(self, task: AgentTask) -> AgentReport:
        """Execute standard agent task and return standard report."""
        start_time = time.time()

        try:
            # Convert to legacy format for compatibility
            result = await self.execute(
                target=task.inputs.get("target", ""),
                description=task.inputs.get("description", ""),
            )

            # Convert legacy result to standard report
            status = TaskStatus.OK if result.success else TaskStatus.FAIL
            report = AgentReport(
                task_id=task.id, status=status, findings=[], changes=[]
            )

            # Add findings from errors/warnings
            for error in result.errors:
                report.add_finding("error", error)
            for warning in result.warnings:
                report.add_finding("warning", warning)

            # Add changes from created/modified files
            for file_path in result.created_files:
                report.add_change("created", file_path, f"Created {file_path}")
            for file_path in result.modified_files:
                report.add_change("modified", file_path, f"Modified {file_path}")

            # Set metrics
            duration = time.time() - start_time
            report.set_duration(duration)

            # Add artifacts
            report.artifacts = result.created_files + result.modified_files

            return report

        except Exception as e:
            # Return failure report
            duration = time.time() - start_time
            report = AgentReport(
                task_id=task.id, status=TaskStatus.FAIL, findings=[], changes=[]
            )
            report.add_finding("error", str(e))
            report.set_duration(duration)
            return report

    def start_task(self, description: str) -> None:
        """Mark the start of a new task."""
        self.current_task_start = time.time()
        console.print(
            f"{self.agent_emoji} [blue]{self.agent_name} received task: {description}[/blue]"
        )

    def create_task_result(
        self,
        success: bool,
        task_description: str,
        created_files: List[str] = None,
        modified_files: List[str] = None,
        errors: List[str] = None,
        warnings: List[str] = None,
        output_data: Dict[str, Any] = None,
        next_recommendations: List[str] = None,
    ) -> AgentReport:
        """Create structured task result."""
        execution_time = time.time() - (self.current_task_start or time.time())

        return AgentReport(
            success=success,
            agent_name=self.agent_name,
            task_description=task_description,
            execution_time=execution_time,
            created_files=created_files or [],
            modified_files=modified_files or [],
            errors=errors or [],
            warnings=warnings or [],
            output_data=output_data or {},
            next_recommendations=next_recommendations or [],
        )

    async def _execute_with_live_display(self, action_text: str, task_func):
        """Execute task with live display."""
        with Live(
            f"{self.agent_emoji} [blue]{action_text}...[/blue]", refresh_per_second=2
        ) as live:
            await asyncio.sleep(1.0)  # Simulate processing
            result = await task_func()
            live.update(f"✅ [green]{self.agent_name} completed successfully![/green]")
            return result

    def log_info(self, message: str):
        """Log informational message."""
        console.print(f"{self.agent_emoji} [blue]{self.agent_name}: {message}[/blue]")

    def log_success(self, message: str):
        """Log success message."""
        console.print(f"✅ [green]{self.agent_name}: {message}[/green]")

    def log_warning(self, message: str):
        """Log warning message."""
        console.print(f"⚠️ [yellow]{self.agent_name}: {message}[/yellow]")

    def log_error(self, message: str):
        """Log error message."""
        console.print(f"❌ [red]{self.agent_name}: {message}[/red]")

    def _initialize_memory(self):
        """Initialize agent memory system."""
        if self.memory_enabled:
            try:
                try:
                    from ..core.agent_memory import get_agent_memory
                except ImportError:
                    from core.agent_memory import get_agent_memory
                self.memory_system = get_agent_memory()
            except ImportError:
                self.memory_enabled = False
                self.memory_system = None

    async def get_intelligent_recommendation(
        self, task_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get intelligent recommendation based on past experiences."""
        if self.memory_enabled and self.memory_system:
            try:
                return self.memory_system.get_recommendation(
                    self.agent_name, task_type, context
                )
            except Exception:
                return None
        return None

    def record_task_experience(
        self,
        task_type: str,
        task_description: str,
        context: Dict[str, Any],
        result: AgentReport,
    ):
        """Record task experience for learning."""
        if self.memory_enabled and self.memory_system:
            try:
                try:
                    from ..core.agent_memory import TaskOutcome
                except ImportError:
                    from core.agent_memory import TaskOutcome

                # Determine outcome
                if result.success and not result.errors:
                    outcome = TaskOutcome.SUCCESS
                elif result.success and result.errors:
                    outcome = TaskOutcome.PARTIAL
                else:
                    outcome = TaskOutcome.FAILURE

                # Record experience
                self.memory_system.record_agent_experience(
                    agent_name=self.agent_name,
                    task_type=task_type,
                    task_description=task_description,
                    context=context,
                    outcome=outcome,
                    execution_time=result.execution_time,
                    success_metrics={
                        "files_created": len(result.created_files),
                        "files_modified": len(result.modified_files),
                        "has_output_data": bool(result.output_data),
                    },
                    errors=result.errors,
                    created_files=result.created_files,
                )
            except Exception:
                # Memory errors shouldn't break the main flow
                pass

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        if self.memory_enabled and self.memory_system:
            try:
                return self.memory_system.get_agent_performance_stats(self.agent_name)
            except Exception:
                return {"error": "Could not retrieve performance stats"}
        return {"message": "Memory system not enabled"}
