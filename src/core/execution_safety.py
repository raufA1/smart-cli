"""Execution Safety System for Smart CLI - Prevents parallel execution conflicts."""

import asyncio
import json
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

console = Console()


class ResourceType(Enum):
    """Types of resources that need protection."""

    FILE = "file"
    DIRECTORY = "directory"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"
    NETWORK = "network"


@dataclass
class ResourceLock:
    """Resource lock for preventing conflicts."""

    resource_id: str
    resource_type: ResourceType
    owner_agent: str
    owner_task_id: str
    lock_time: float
    exclusive: bool = True  # True for exclusive, False for shared

    def is_expired(self, timeout: float = 300.0) -> bool:
        """Check if lock is expired (5 minute default timeout)."""
        return time.time() - self.lock_time > timeout


class ExecutionSafetyManager:
    """Advanced safety manager for parallel execution."""

    def __init__(self):
        # Resource locking
        self.resource_locks: Dict[str, ResourceLock] = {}
        self.lock_timeout = 300.0  # 5 minutes
        self._lock_mutex = threading.Lock()

        # File system monitoring
        self.file_operations: Dict[str, List[str]] = {}  # file -> [agent_names]
        self.protected_files: Set[str] = set()

        # API rate limiting
        self.api_request_counts: Dict[str, List[float]] = {}  # endpoint -> [timestamps]
        self.api_rate_limits = {
            "openrouter": 60,  # requests per minute
            "anthropic": 50,
            "openai": 90,
        }

        # Agent coordination
        self.agent_dependencies: Dict[str, Set[str]] = {}
        self.execution_order: List[str] = []

        # Safety statistics
        self.conflict_prevention_stats = {
            "file_conflicts_prevented": 0,
            "api_rate_limits_avoided": 0,
            "dependency_violations_blocked": 0,
            "total_safety_interventions": 0,
        }

    def register_agent_dependencies(self, agent_name: str, dependencies: List[str]):
        """Register what other agents this agent depends on."""
        self.agent_dependencies[agent_name] = set(dependencies)

    def check_execution_safety(
        self,
        agent_name: str,
        task_id: str,
        target_files: List[str],
        api_calls: List[str] = None,
    ) -> Dict[str, Any]:
        """Check if it's safe to execute agent task."""
        safety_report = {
            "safe_to_execute": True,
            "warnings": [],
            "blocked_reasons": [],
            "recommended_delay": 0,
            "resource_conflicts": [],
        }

        # Check file conflicts
        file_conflicts = self._check_file_conflicts(agent_name, task_id, target_files)
        if file_conflicts:
            safety_report["safe_to_execute"] = False
            safety_report["blocked_reasons"].extend(file_conflicts)
            safety_report["resource_conflicts"].extend(file_conflicts)

        # Check API rate limits
        api_delays = self._check_api_rate_limits(api_calls or [])
        if api_delays:
            max_delay = max(api_delays.values())
            if max_delay > 0:
                safety_report["recommended_delay"] = max_delay
                safety_report["warnings"].append(
                    f"API rate limit: wait {max_delay:.1f}s"
                )

        # Check agent dependencies
        dependency_issues = self._check_agent_dependencies(agent_name)
        if dependency_issues:
            safety_report["safe_to_execute"] = False
            safety_report["blocked_reasons"].extend(dependency_issues)

        return safety_report

    def _check_file_conflicts(
        self, agent_name: str, task_id: str, target_files: List[str]
    ) -> List[str]:
        """Check for file access conflicts."""
        conflicts = []

        for file_path in target_files:
            normalized_path = os.path.normpath(file_path)

            # Check if file is already locked
            if normalized_path in self.resource_locks:
                existing_lock = self.resource_locks[normalized_path]

                # Skip if it's our own lock
                if existing_lock.owner_task_id == task_id:
                    continue

                # Check if lock is expired
                if existing_lock.is_expired(self.lock_timeout):
                    self._release_resource_lock(normalized_path)
                    continue

                # Check if we can get shared access
                if not existing_lock.exclusive and self._is_read_only_operation(
                    agent_name
                ):
                    continue

                conflicts.append(
                    f"File conflict: {normalized_path} locked by {existing_lock.owner_agent}"
                )
                self.conflict_prevention_stats["file_conflicts_prevented"] += 1

        return conflicts

    def _check_api_rate_limits(self, api_calls: List[str]) -> Dict[str, float]:
        """Check API rate limits and return required delays."""
        delays = {}
        current_time = time.time()

        for api_endpoint in api_calls:
            # Clean old timestamps
            if api_endpoint in self.api_request_counts:
                self.api_request_counts[api_endpoint] = [
                    ts
                    for ts in self.api_request_counts[api_endpoint]
                    if current_time - ts < 60  # Keep last minute
                ]

            # Check rate limit
            provider = self._get_api_provider(api_endpoint)
            if provider in self.api_rate_limits:
                recent_requests = len(self.api_request_counts.get(api_endpoint, []))
                rate_limit = self.api_rate_limits[provider]

                if recent_requests >= rate_limit:
                    # Calculate delay needed
                    oldest_request = min(self.api_request_counts[api_endpoint])
                    delay_needed = 60 - (current_time - oldest_request)
                    delays[api_endpoint] = max(0, delay_needed)

                    self.conflict_prevention_stats["api_rate_limits_avoided"] += 1

        return delays

    def _check_agent_dependencies(self, agent_name: str) -> List[str]:
        """Check if agent dependencies are satisfied."""
        issues = []

        if agent_name in self.agent_dependencies:
            for dependency in self.agent_dependencies[agent_name]:
                # Check if dependency agent has completed
                if not self._is_agent_completed(dependency):
                    issues.append(
                        f"Dependency violation: {agent_name} depends on {dependency}"
                    )
                    self.conflict_prevention_stats["dependency_violations_blocked"] += 1

        return issues

    def acquire_resource_lock(
        self,
        agent_name: str,
        task_id: str,
        resource_path: str,
        resource_type: ResourceType,
        exclusive: bool = True,
    ) -> bool:
        """Acquire lock on resource."""
        with self._lock_mutex:
            normalized_path = os.path.normpath(resource_path)

            # Check if already locked
            if normalized_path in self.resource_locks:
                existing_lock = self.resource_locks[normalized_path]

                # Skip if it's our own lock
                if existing_lock.owner_task_id == task_id:
                    return True

                # Check if expired
                if existing_lock.is_expired(self.lock_timeout):
                    self._release_resource_lock(normalized_path)
                else:
                    # Check if we can get shared access
                    if not existing_lock.exclusive and not exclusive:
                        # Create shared lock record (don't override existing)
                        return True
                    else:
                        return False

            # Create new lock
            self.resource_locks[normalized_path] = ResourceLock(
                resource_id=normalized_path,
                resource_type=resource_type,
                owner_agent=agent_name,
                owner_task_id=task_id,
                lock_time=time.time(),
                exclusive=exclusive,
            )

            console.print(
                f"🔒 [blue]Lock acquired: {agent_name} → {normalized_path}[/blue]"
            )
            return True

    def release_resource_lock(self, task_id: str, resource_path: str):
        """Release resource lock."""
        with self._lock_mutex:
            normalized_path = os.path.normpath(resource_path)

            if normalized_path in self.resource_locks:
                lock = self.resource_locks[normalized_path]
                if lock.owner_task_id == task_id:
                    self._release_resource_lock(normalized_path)
                    console.print(
                        f"🔓 [green]Lock released: {lock.owner_agent} → {normalized_path}[/green]"
                    )

    def _release_resource_lock(self, resource_path: str):
        """Internal method to release resource lock."""
        if resource_path in self.resource_locks:
            del self.resource_locks[resource_path]

    def release_all_locks_for_task(self, task_id: str):
        """Release all locks held by a task."""
        with self._lock_mutex:
            locks_to_release = []

            for resource_path, lock in self.resource_locks.items():
                if lock.owner_task_id == task_id:
                    locks_to_release.append(resource_path)

            for resource_path in locks_to_release:
                self._release_resource_lock(resource_path)
                console.print(f"🔓 [green]Auto-released lock: {resource_path}[/green]")

    def record_api_request(self, api_endpoint: str):
        """Record API request for rate limiting."""
        current_time = time.time()

        if api_endpoint not in self.api_request_counts:
            self.api_request_counts[api_endpoint] = []

        self.api_request_counts[api_endpoint].append(current_time)

        # Clean old entries
        self.api_request_counts[api_endpoint] = [
            ts for ts in self.api_request_counts[api_endpoint] if current_time - ts < 60
        ]

    def _get_api_provider(self, api_endpoint: str) -> str:
        """Get API provider from endpoint."""
        if "openrouter" in api_endpoint:
            return "openrouter"
        elif "anthropic" in api_endpoint:
            return "anthropic"
        elif "openai" in api_endpoint:
            return "openai"
        else:
            return "unknown"

    def _is_read_only_operation(self, agent_name: str) -> bool:
        """Check if agent performs read-only operations."""
        read_only_agents = ["analyzer", "reviewer"]
        return agent_name.lower() in read_only_agents

    def _is_agent_completed(self, agent_name: str) -> bool:
        """Check if agent has completed its tasks."""
        # This would be implemented with actual agent status tracking
        # For now, we'll assume all agents start as not completed
        return False

    def create_safe_execution_plan(
        self, agent_tasks: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Create safe execution plan with phases to avoid conflicts."""

        # Phase 1: Read-only operations (Analysis, Review)
        read_only_phase = []

        # Phase 2: Architecture and planning
        planning_phase = []

        # Phase 3: Implementation
        implementation_phase = []

        # Phase 4: Testing and validation
        testing_phase = []

        for task in agent_tasks:
            agent = task.get("agent", "").lower()

            if agent in ["analyzer", "reviewer"]:
                read_only_phase.append(task)
            elif agent in ["architect"]:
                planning_phase.append(task)
            elif agent in ["modifier"]:
                implementation_phase.append(task)
            elif agent in ["tester"]:
                testing_phase.append(task)
            else:
                # Default to implementation phase
                implementation_phase.append(task)

        # Create execution phases (non-empty phases only)
        execution_phases = []
        if read_only_phase:
            execution_phases.append(read_only_phase)
        if planning_phase:
            execution_phases.append(planning_phase)
        if implementation_phase:
            execution_phases.append(implementation_phase)
        if testing_phase:
            execution_phases.append(testing_phase)

        console.print(
            f"🛡️ [blue]Created {len(execution_phases)} safe execution phases[/blue]"
        )

        return execution_phases

    def get_safety_statistics(self) -> Dict[str, Any]:
        """Get safety intervention statistics."""
        total_interventions = sum(self.conflict_prevention_stats.values())

        return {
            "safety_interventions": self.conflict_prevention_stats,
            "total_interventions": total_interventions,
            "active_locks": len(self.resource_locks),
            "protected_resources": list(self.resource_locks.keys()),
            "api_monitoring": {
                endpoint: len(requests)
                for endpoint, requests in self.api_request_counts.items()
            },
        }

    def cleanup_expired_locks(self):
        """Clean up expired resource locks."""
        with self._lock_mutex:
            expired_locks = []

            for resource_path, lock in self.resource_locks.items():
                if lock.is_expired(self.lock_timeout):
                    expired_locks.append(resource_path)

            for resource_path in expired_locks:
                self._release_resource_lock(resource_path)
                console.print(
                    f"🧹 [yellow]Cleaned expired lock: {resource_path}[/yellow]"
                )

    async def safe_parallel_execution_wrapper(
        self,
        task_execution_func,
        agent_name: str,
        task_id: str,
        target_files: List[str] = None,
        api_calls: List[str] = None,
    ):
        """Wrapper for safe task execution with automatic lock management."""
        target_files = target_files or []
        api_calls = api_calls or []

        try:
            # Check safety first
            safety_check = self.check_execution_safety(
                agent_name, task_id, target_files, api_calls
            )

            if not safety_check["safe_to_execute"]:
                console.print(f"🚫 [red]Execution blocked for {agent_name}:[/red]")
                for reason in safety_check["blocked_reasons"]:
                    console.print(f"   - {reason}")
                return None

            # Wait for recommended delay
            if safety_check["recommended_delay"] > 0:
                console.print(
                    f"⏳ [yellow]Waiting {safety_check['recommended_delay']:.1f}s for safety...[/yellow]"
                )
                await asyncio.sleep(safety_check["recommended_delay"])

            # Acquire locks
            locks_acquired = []
            for file_path in target_files:
                if self.acquire_resource_lock(
                    agent_name, task_id, file_path, ResourceType.FILE
                ):
                    locks_acquired.append(file_path)
                else:
                    # Release acquired locks and fail
                    for acquired_file in locks_acquired:
                        self.release_resource_lock(task_id, acquired_file)
                    console.print(
                        f"❌ [red]Could not acquire all locks for {agent_name}[/red]"
                    )
                    return None

            # Record API requests
            for api_call in api_calls:
                self.record_api_request(api_call)

            # Execute task
            result = await task_execution_func()

            return result

        finally:
            # Always release locks
            self.release_all_locks_for_task(task_id)


# Global safety manager
_global_safety_manager = None


def get_execution_safety_manager() -> ExecutionSafetyManager:
    """Get global execution safety manager."""
    global _global_safety_manager
    if _global_safety_manager is None:
        _global_safety_manager = ExecutionSafetyManager()
    return _global_safety_manager
