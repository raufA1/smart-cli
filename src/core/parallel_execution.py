"""Parallel Agent Execution System for Smart CLI."""

import asyncio
import concurrent.futures
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()


class TaskPriority(Enum):
    """Task priority levels for execution."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ParallelTask:
    """Task for parallel execution."""

    task_id: str
    agent_name: str
    target: str
    description: str
    action: str
    priority: TaskPriority
    dependencies: List[str]  # Task IDs that must complete first
    estimated_time: float
    context: Dict[str, Any]
    created_at: float

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()


@dataclass
class TaskResult:
    """Result from parallel task execution."""

    task_id: str
    agent_name: str
    success: bool
    result_data: Any
    execution_time: float
    error: Optional[str] = None


class ParallelExecutionManager:
    """Advanced parallel execution manager for agents."""

    def __init__(self, max_concurrent_tasks: int = 3, max_workers: int = 2):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_workers = max_workers

        # Task management
        self.pending_tasks: List[ParallelTask] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}

        # Execution state
        self.is_running = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

        # Performance tracking
        self.execution_stats = {
            "total_tasks_processed": 0,
            "average_execution_time": 0,
            "parallel_efficiency": 0,
            "resource_utilization": 0,
        }

    def add_task(self, task: ParallelTask) -> str:
        """Add task to execution queue."""
        # Check for duplicate task IDs
        if task.task_id in [t.task_id for t in self.pending_tasks]:
            task.task_id = f"{task.task_id}_{int(time.time())}"

        self.pending_tasks.append(task)
        console.print(
            f"📝 [blue]Added task: {task.agent_name} - {task.description[:50]}...[/blue]"
        )

        return task.task_id

    def create_agent_task(
        self,
        agent_name: str,
        target: str,
        description: str,
        action: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: List[str] = None,
        estimated_time: float = 30.0,
        context: Dict[str, Any] = None,
    ) -> str:
        """Create and add agent task."""
        task_id = f"{agent_name}_{int(time.time())}_{hash(description) % 10000}"

        task = ParallelTask(
            task_id=task_id,
            agent_name=agent_name,
            target=target,
            description=description,
            action=action,
            priority=priority,
            dependencies=dependencies or [],
            estimated_time=estimated_time,
            context=context or {},
            created_at=time.time(),
        )

        return self.add_task(task)

    def _can_execute_task(self, task: ParallelTask) -> bool:
        """Check if task can be executed (dependencies met)."""
        for dependency_id in task.dependencies:
            if dependency_id not in self.completed_tasks:
                return False
        return True

    def _get_next_tasks(self) -> List[ParallelTask]:
        """Get next tasks ready for execution based on dependencies and priority."""
        available_slots = self.max_concurrent_tasks - len(self.running_tasks)
        if available_slots <= 0:
            return []

        # Filter executable tasks
        executable_tasks = [
            task for task in self.pending_tasks if self._can_execute_task(task)
        ]

        if not executable_tasks:
            return []

        # Sort by priority then by creation time
        executable_tasks.sort(
            key=lambda t: (t.priority.value, t.created_at), reverse=True
        )

        return executable_tasks[:available_slots]

    async def _execute_single_task(
        self, task: ParallelTask, orchestrator
    ) -> TaskResult:
        """Execute single task with safety checks and proper error handling."""
        start_time = time.time()

        try:
            # Import safety manager
            from .execution_safety import get_execution_safety_manager

            safety_manager = get_execution_safety_manager()

            # Define task execution function for safety wrapper
            async def execute_task():
                # Get agent from orchestrator
                if (
                    hasattr(orchestrator, "agents")
                    and task.agent_name in orchestrator.agents
                ):
                    agent = orchestrator.agents[task.agent_name]

                    # Execute agent task
                    result = await agent.execute(task.target, task.description)
                    return result
                else:
                    # Fallback to orchestrator delegation
                    result = await orchestrator.delegate_to_agent(
                        task.agent_name, task.target, task.description, task.action
                    )
                    return result

            # Determine target files and API calls for safety check
            target_files = [task.target] if task.target != "." else []
            api_calls = (
                ["openrouter.ai/api/v1"] if hasattr(orchestrator, "ai_client") else []
            )

            # Execute with safety wrapper
            result = await safety_manager.safe_parallel_execution_wrapper(
                execute_task,
                task.agent_name,
                task.task_id,
                target_files=target_files,
                api_calls=api_calls,
            )

            execution_time = time.time() - start_time

            if result:
                return TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=getattr(result, "success", True),
                    result_data=result,
                    execution_time=execution_time,
                )
            else:
                return TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=False,
                    result_data=None,
                    execution_time=execution_time,
                    error="Safety check failed or resource conflict",
                )

        except Exception as e:
            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                result_data=None,
                execution_time=execution_time,
                error=str(e),
            )

    async def execute_parallel(
        self, orchestrator, progress_callback: Callable = None
    ) -> Dict[str, TaskResult]:
        """Execute all tasks in parallel with intelligent scheduling."""
        if not self.pending_tasks:
            console.print("⚠️ [yellow]No tasks to execute[/yellow]")
            return {}

        self.is_running = True
        total_tasks = len(self.pending_tasks)

        console.print(
            f"🚀 [bold blue]Starting parallel execution: {total_tasks} tasks[/bold blue]"
        )

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            main_progress = progress.add_task("Parallel Execution", total=total_tasks)

            # Main execution loop
            while self.pending_tasks or self.running_tasks:
                # Start new tasks if possible
                next_tasks = self._get_next_tasks()

                for task in next_tasks:
                    # Remove from pending
                    self.pending_tasks.remove(task)

                    # Start task
                    task_coroutine = self._execute_single_task(task, orchestrator)
                    async_task = asyncio.create_task(task_coroutine)
                    self.running_tasks[task.task_id] = async_task

                    console.print(
                        f"▶️ [green]Starting: {task.agent_name} - {task.description[:40]}...[/green]"
                    )

                # Wait for at least one task to complete
                if self.running_tasks:
                    done, pending = await asyncio.wait(
                        self.running_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=1.0,
                    )

                    # Process completed tasks
                    for completed_task in done:
                        # Find task ID
                        task_id = None
                        for tid, task in self.running_tasks.items():
                            if task == completed_task:
                                task_id = tid
                                break

                        if task_id:
                            try:
                                result = await completed_task

                                if result.success:
                                    self.completed_tasks[task_id] = result
                                    console.print(
                                        f"✅ [green]Completed: {result.agent_name} ({result.execution_time:.1f}s)[/green]"
                                    )
                                else:
                                    self.failed_tasks[task_id] = result
                                    console.print(
                                        f"❌ [red]Failed: {result.agent_name} - {result.error or 'Unknown error'}[/red]"
                                    )

                                # Update progress
                                progress.update(main_progress, advance=1)

                                # Call progress callback if provided
                                if progress_callback:
                                    await progress_callback(result)

                            except Exception as e:
                                console.print(
                                    f"❌ [red]Task execution error: {str(e)}[/red]"
                                )

                            # Remove from running tasks
                            del self.running_tasks[task_id]

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

        self.is_running = False

        # Calculate and update statistics
        self._update_execution_stats()

        # Return all results
        all_results = {**self.completed_tasks, **self.failed_tasks}

        console.print(f"🏁 [bold green]Parallel execution completed![/bold green]")
        console.print(f"   ✅ Successful: {len(self.completed_tasks)}")
        console.print(f"   ❌ Failed: {len(self.failed_tasks)}")
        console.print(
            f"   ⚡ Efficiency: {self.execution_stats['parallel_efficiency']:.1f}%"
        )

        return all_results

    def _update_execution_stats(self):
        """Update execution performance statistics."""
        all_results = list(self.completed_tasks.values()) + list(
            self.failed_tasks.values()
        )

        if not all_results:
            return

        # Calculate statistics
        total_execution_time = sum(result.execution_time for result in all_results)
        self.execution_stats["average_execution_time"] = total_execution_time / len(
            all_results
        )

        # Calculate parallel efficiency
        sequential_time = sum(result.execution_time for result in all_results)
        actual_wall_time = (
            max(result.execution_time for result in all_results)
            if all_results
            else sequential_time
        )

        if actual_wall_time > 0:
            self.execution_stats["parallel_efficiency"] = (
                sequential_time / actual_wall_time
            ) * 100

        self.execution_stats["total_tasks_processed"] += len(all_results)

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution performance summary."""
        return {
            "total_tasks": len(self.completed_tasks) + len(self.failed_tasks),
            "successful_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "success_rate": (
                len(self.completed_tasks)
                / (len(self.completed_tasks) + len(self.failed_tasks))
                if (len(self.completed_tasks) + len(self.failed_tasks)) > 0
                else 0
            ),
            "execution_stats": self.execution_stats,
            "currently_running": len(self.running_tasks),
            "pending_tasks": len(self.pending_tasks),
        }

    async def cancel_all_tasks(self):
        """Cancel all running and pending tasks."""
        console.print("🛑 [yellow]Canceling all tasks...[/yellow]")

        # Cancel running tasks
        for task in self.running_tasks.values():
            task.cancel()

        # Wait for cancellations
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        # Clear all task lists
        self.pending_tasks.clear()
        self.running_tasks.clear()

        self.is_running = False
        console.print("✅ [green]All tasks canceled[/green]")

    def create_dependency_chain(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Create a chain of dependent tasks."""
        task_ids = []
        previous_task_id = None

        for i, task_info in enumerate(tasks):
            dependencies = [previous_task_id] if previous_task_id else []

            task_id = self.create_agent_task(
                agent_name=task_info["agent_name"],
                target=task_info.get("target", "."),
                description=task_info["description"],
                action=task_info.get("action", ""),
                priority=TaskPriority(task_info.get("priority", 2)),
                dependencies=dependencies,
                estimated_time=task_info.get("estimated_time", 30.0),
                context=task_info.get("context", {}),
            )

            task_ids.append(task_id)
            previous_task_id = task_id

        return task_ids

    def create_parallel_batch(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Create a batch of parallel tasks (no dependencies)."""
        task_ids = []

        for task_info in tasks:
            task_id = self.create_agent_task(
                agent_name=task_info["agent_name"],
                target=task_info.get("target", "."),
                description=task_info["description"],
                action=task_info.get("action", ""),
                priority=TaskPriority(task_info.get("priority", 2)),
                dependencies=[],  # No dependencies for parallel batch
                estimated_time=task_info.get("estimated_time", 30.0),
                context=task_info.get("context", {}),
            )

            task_ids.append(task_id)

        return task_ids

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
