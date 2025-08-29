"""Intelligent Execution Planner - Smart agent scheduling with dependency management."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# import networkx as nx  # Using simple dependency resolution instead
from rich.console import Console

console = Console()


class AgentCapability(Enum):
    """Agent capabilities for intelligent planning."""

    READ_ONLY = "read_only"  # Can read files safely
    FILE_CREATION = "file_creation"  # Creates new files
    FILE_MODIFICATION = "file_modification"  # Modifies existing files
    ANALYSIS = "analysis"  # Analyzes code/projects
    ARCHITECTURE = "architecture"  # Designs system structure
    CODE_GENERATION = "code_generation"  # Generates code
    TESTING = "testing"  # Runs tests
    REVIEW = "review"  # Reviews code quality


class ExecutionMode(Enum):
    """Execution modes for different scenarios."""

    SEQUENTIAL = "sequential"  # One by one execution
    PARALLEL_SAFE = "parallel_safe"  # Parallel with no conflicts
    HYBRID = "hybrid"  # Mix of sequential and parallel


@dataclass
class AgentProfile:
    """Comprehensive agent profile for intelligent planning."""

    name: str
    capabilities: List[AgentCapability]
    dependencies: List[str]  # Which agents must run before this one
    conflicts_with: List[str]  # Which agents cannot run simultaneously
    resource_requirements: List[str]  # What resources this agent needs
    execution_time_estimate: float  # Estimated execution time
    parallel_safe: bool = False  # Can this agent run in parallel?
    priority_level: int = 1  # 1=low, 5=critical


@dataclass
class ExecutionPhase:
    """A phase in the execution plan."""

    phase_number: int
    agents: List[str]
    execution_mode: ExecutionMode
    estimated_duration: float
    dependencies_satisfied: List[str]
    resource_locks_needed: List[str]


class IntelligentExecutionPlanner:
    """Advanced execution planner with dependency management."""

    def __init__(self):
        # Agent profiles with detailed capabilities
        self.agent_profiles = {
            "analyzer": AgentProfile(
                name="analyzer",
                capabilities=[AgentCapability.READ_ONLY, AgentCapability.ANALYSIS],
                dependencies=[],  # No dependencies - can run first
                conflicts_with=[],  # Safe with everyone
                resource_requirements=["project_files"],
                execution_time_estimate=30.0,
                parallel_safe=True,  # Can run with other read-only agents
                priority_level=2,
            ),
            "architect": AgentProfile(
                name="architect",
                capabilities=[AgentCapability.ARCHITECTURE, AgentCapability.ANALYSIS],
                dependencies=["analyzer"],  # Needs analysis first
                conflicts_with=[],
                resource_requirements=["project_files"],
                execution_time_estimate=45.0,
                parallel_safe=False,  # Architecture should be planned alone
                priority_level=4,  # High priority
            ),
            "modifier": AgentProfile(
                name="modifier",
                capabilities=[
                    AgentCapability.FILE_CREATION,
                    AgentCapability.FILE_MODIFICATION,
                    AgentCapability.CODE_GENERATION,
                ],
                dependencies=["architect"],  # Needs architecture first
                conflicts_with=[
                    "tester"
                ],  # Cannot run while tester is testing same files
                resource_requirements=["file_system_write"],
                execution_time_estimate=60.0,
                parallel_safe=False,  # File creation is sensitive
                priority_level=3,
            ),
            "tester": AgentProfile(
                name="tester",
                capabilities=[AgentCapability.TESTING],
                dependencies=["modifier"],  # Needs files to test
                conflicts_with=[
                    "modifier"
                ],  # Cannot test while files are being modified
                resource_requirements=["file_system_read", "test_environment"],
                execution_time_estimate=35.0,
                parallel_safe=True,  # Can run with reviewer
                priority_level=2,
            ),
            "reviewer": AgentProfile(
                name="reviewer",
                capabilities=[AgentCapability.READ_ONLY, AgentCapability.REVIEW],
                dependencies=["modifier"],  # Needs code to review
                conflicts_with=[],  # Safe with everyone (read-only)
                resource_requirements=["project_files"],
                execution_time_estimate=25.0,
                parallel_safe=True,  # Safe to run in parallel
                priority_level=1,
            ),
        }

        # Execution scenarios with different strategies
        self.execution_scenarios = {
            "simple_analysis": {"agents": ["analyzer"], "strategy": "single_agent"},
            "quick_review": {
                "agents": ["analyzer", "reviewer"],
                "strategy": "parallel_readonly",
            },
            "full_implementation": {
                "agents": ["analyzer", "architect", "modifier", "tester", "reviewer"],
                "strategy": "smart_pipeline",
            },
            "code_generation": {
                "agents": ["analyzer", "modifier"],
                "strategy": "sequential_creation",
            },
        }

    def create_intelligent_execution_plan(
        self, agent_tasks: List[Dict[str, Any]], scenario_hint: str = None
    ) -> List[ExecutionPhase]:
        """Create intelligent execution plan based on agent dependencies and capabilities."""

        console.print(
            f"🧠 [bold blue]Creating intelligent execution plan...[/bold blue]"
        )

        # Extract agent names from tasks
        agent_names = [task.get("agent") for task in agent_tasks]

        # Detect scenario if not provided
        if not scenario_hint:
            scenario_hint = self._detect_execution_scenario(agent_names)

        console.print(f"📋 [blue]Detected scenario: {scenario_hint}[/blue]")

        # Create dependency graph
        dependency_graph = self._create_dependency_graph(agent_names)

        # Generate execution phases using topological sort
        execution_phases = self._generate_execution_phases(
            dependency_graph, agent_tasks
        )

        # Optimize for parallel execution where safe
        optimized_phases = self._optimize_for_parallel_execution(execution_phases)

        # Display execution plan
        self._display_execution_plan(optimized_phases)

        return optimized_phases

    def _detect_execution_scenario(self, agent_names: List[str]) -> str:
        """Detect execution scenario based on agent combination."""
        agent_set = set(agent_names)

        # Check for known scenarios
        for scenario, config in self.execution_scenarios.items():
            if set(config["agents"]) == agent_set:
                return scenario

        # Classify based on agent types
        if len(agent_names) == 1:
            return "single_agent"
        elif all(
            self.agent_profiles[agent].parallel_safe
            for agent in agent_names
            if agent in self.agent_profiles
        ):
            return "parallel_readonly"
        elif "modifier" in agent_names and "tester" in agent_names:
            return "full_implementation"
        else:
            return "custom_scenario"

    def _create_dependency_graph(self, agent_names: List[str]) -> Dict[str, List[str]]:
        """Create dependency graph using simple dictionary structure."""
        graph = {}

        # Initialize graph
        for agent in agent_names:
            if agent in self.agent_profiles:
                graph[agent] = self.agent_profiles[agent].dependencies.copy()

        return graph

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Simple topological sort implementation."""
        # Calculate in-degrees
        in_degree = {node: 0 for node in graph}

        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find nodes with no incoming edges
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Remove edges from this node
            for dependent in graph:
                if node in graph[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check if all nodes are processed (no cycles)
        if len(result) != len(graph):
            return []  # Cycle detected

        return result

    def _generate_execution_phases(
        self, dependency_graph: Dict[str, List[str]], agent_tasks: List[Dict[str, Any]]
    ) -> List[ExecutionPhase]:
        """Generate execution phases using simple topological sorting."""
        # Simple topological sort implementation
        topo_order = self._topological_sort(dependency_graph)

        if not topo_order:
            console.print(
                "⚠️ [yellow]Circular dependency detected, using fallback ordering[/yellow]"
            )
            topo_order = list(dependency_graph.keys())

        # Create task mapping
        task_map = {task.get("agent"): task for task in agent_tasks}

        # Group agents into phases based on dependencies and conflicts
        phases = []
        processed_agents = set()

        phase_number = 1

        while len(processed_agents) < len(topo_order):
            current_phase_agents = []

            for agent in topo_order:
                if agent in processed_agents:
                    continue

                # Check if all dependencies are satisfied
                if agent in self.agent_profiles:
                    profile = self.agent_profiles[agent]
                    dependencies_satisfied = all(
                        dep in processed_agents or dep not in topo_order
                        for dep in profile.dependencies
                    )

                    if dependencies_satisfied:
                        # Check conflicts with agents already in current phase
                        has_conflicts = any(
                            conflict in current_phase_agents
                            for conflict in profile.conflicts_with
                        )

                        if not has_conflicts:
                            current_phase_agents.append(agent)

            if current_phase_agents:
                # Determine execution mode for this phase
                execution_mode = self._determine_phase_execution_mode(
                    current_phase_agents
                )

                # Calculate estimated duration
                estimated_duration = self._calculate_phase_duration(
                    current_phase_agents, execution_mode
                )

                # Get satisfied dependencies
                satisfied_deps = list(processed_agents)

                # Get resource locks needed
                resource_locks = self._get_required_resource_locks(current_phase_agents)

                phase = ExecutionPhase(
                    phase_number=phase_number,
                    agents=current_phase_agents,
                    execution_mode=execution_mode,
                    estimated_duration=estimated_duration,
                    dependencies_satisfied=satisfied_deps,
                    resource_locks_needed=resource_locks,
                )

                phases.append(phase)
                processed_agents.update(current_phase_agents)
                phase_number += 1
            else:
                # No agents can be processed - break to avoid infinite loop
                remaining = set(topo_order) - processed_agents
                console.print(
                    f"⚠️ [yellow]Cannot process remaining agents: {remaining}[/yellow]"
                )
                break

        return phases

    def _determine_phase_execution_mode(self, agents: List[str]) -> ExecutionMode:
        """Determine execution mode for a phase."""
        if len(agents) == 1:
            return ExecutionMode.SEQUENTIAL

        # Check if all agents in phase are parallel-safe
        all_parallel_safe = all(
            self.agent_profiles[agent].parallel_safe
            for agent in agents
            if agent in self.agent_profiles
        )

        if all_parallel_safe:
            return ExecutionMode.PARALLEL_SAFE
        else:
            return ExecutionMode.HYBRID

    def _calculate_phase_duration(
        self, agents: List[str], execution_mode: ExecutionMode
    ) -> float:
        """Calculate estimated phase duration."""
        if not agents:
            return 0.0

        execution_times = [
            self.agent_profiles[agent].execution_time_estimate
            for agent in agents
            if agent in self.agent_profiles
        ]

        if execution_mode == ExecutionMode.PARALLEL_SAFE:
            # Parallel execution - duration is the maximum time
            return max(execution_times) if execution_times else 30.0
        else:
            # Sequential execution - duration is sum of times
            return sum(execution_times) if execution_times else 30.0

    def _get_required_resource_locks(self, agents: List[str]) -> List[str]:
        """Get required resource locks for agents in phase."""
        resource_locks = set()

        for agent in agents:
            if agent in self.agent_profiles:
                resource_locks.update(self.agent_profiles[agent].resource_requirements)

        return list(resource_locks)

    def _optimize_for_parallel_execution(
        self, phases: List[ExecutionPhase]
    ) -> List[ExecutionPhase]:
        """Optimize phases for better parallel execution."""
        optimized_phases = []

        for phase in phases:
            # Check if we can split phase for better parallelization
            if len(phase.agents) > 1 and phase.execution_mode == ExecutionMode.HYBRID:

                # Separate parallel-safe from non-parallel-safe agents
                parallel_safe_agents = []
                non_parallel_safe_agents = []

                for agent in phase.agents:
                    if agent in self.agent_profiles:
                        if self.agent_profiles[agent].parallel_safe:
                            parallel_safe_agents.append(agent)
                        else:
                            non_parallel_safe_agents.append(agent)

                # Create separate phases if beneficial
                if parallel_safe_agents and non_parallel_safe_agents:
                    # Phase for parallel-safe agents
                    if parallel_safe_agents:
                        parallel_phase = ExecutionPhase(
                            phase_number=phase.phase_number,
                            agents=parallel_safe_agents,
                            execution_mode=ExecutionMode.PARALLEL_SAFE,
                            estimated_duration=self._calculate_phase_duration(
                                parallel_safe_agents, ExecutionMode.PARALLEL_SAFE
                            ),
                            dependencies_satisfied=phase.dependencies_satisfied,
                            resource_locks_needed=self._get_required_resource_locks(
                                parallel_safe_agents
                            ),
                        )
                        optimized_phases.append(parallel_phase)

                    # Phase for non-parallel-safe agents
                    if non_parallel_safe_agents:
                        sequential_phase = ExecutionPhase(
                            phase_number=phase.phase_number + 0.5,  # Sub-phase
                            agents=non_parallel_safe_agents,
                            execution_mode=ExecutionMode.SEQUENTIAL,
                            estimated_duration=self._calculate_phase_duration(
                                non_parallel_safe_agents, ExecutionMode.SEQUENTIAL
                            ),
                            dependencies_satisfied=phase.dependencies_satisfied
                            + parallel_safe_agents,
                            resource_locks_needed=self._get_required_resource_locks(
                                non_parallel_safe_agents
                            ),
                        )
                        optimized_phases.append(sequential_phase)
                else:
                    optimized_phases.append(phase)
            else:
                optimized_phases.append(phase)

        return optimized_phases

    def _display_execution_plan(self, phases: List[ExecutionPhase]):
        """Display the execution plan in a readable format."""
        console.print("\n📋 [bold blue]INTELLIGENT EXECUTION PLAN[/bold blue]")
        console.print("=" * 60)

        total_duration = 0

        for phase in phases:
            console.print(
                f"\n🔸 [bold yellow]Phase {phase.phase_number:.1f}[/bold yellow] - {phase.execution_mode.value.upper()}"
            )
            console.print(f"   Agents: {', '.join(phase.agents)}")
            console.print(f"   Duration: {phase.estimated_duration:.1f}s")
            console.print(
                f"   Dependencies: {', '.join(phase.dependencies_satisfied) if phase.dependencies_satisfied else 'None'}"
            )

            if phase.execution_mode == ExecutionMode.PARALLEL_SAFE:
                console.print("   ⚡ [green]Parallel execution (safe)[/green]")
            elif phase.execution_mode == ExecutionMode.SEQUENTIAL:
                console.print("   🔄 [blue]Sequential execution[/blue]")
            else:
                console.print("   🔀 [yellow]Hybrid execution[/yellow]")

            total_duration += phase.estimated_duration

        console.print(
            f"\n⏱️ [bold green]Total Estimated Duration: {total_duration:.1f}s[/bold green]"
        )
        console.print("=" * 60)

    def validate_execution_plan(self, phases: List[ExecutionPhase]) -> Dict[str, Any]:
        """Validate the execution plan for correctness."""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "optimization_suggestions": [],
        }

        all_agents_in_plan = set()
        processed_agents = set()

        for phase in phases:
            all_agents_in_plan.update(phase.agents)

            # Check dependency satisfaction
            for agent in phase.agents:
                if agent in self.agent_profiles:
                    profile = self.agent_profiles[agent]

                    # Check if dependencies are satisfied
                    unsatisfied_deps = [
                        dep
                        for dep in profile.dependencies
                        if dep not in processed_agents and dep in all_agents_in_plan
                    ]

                    if unsatisfied_deps:
                        validation_result["errors"].append(
                            f"Agent {agent} has unsatisfied dependencies: {unsatisfied_deps}"
                        )
                        validation_result["valid"] = False

            # Check for conflicts within phase
            if phase.execution_mode == ExecutionMode.PARALLEL_SAFE:
                for agent in phase.agents:
                    if agent in self.agent_profiles:
                        profile = self.agent_profiles[agent]
                        conflicts_in_phase = [
                            conflict
                            for conflict in profile.conflicts_with
                            if conflict in phase.agents
                        ]

                        if conflicts_in_phase:
                            validation_result["errors"].append(
                                f"Agent {agent} conflicts with {conflicts_in_phase} in same parallel phase"
                            )
                            validation_result["valid"] = False

            processed_agents.update(phase.agents)

        # Check for optimization opportunities
        parallel_phases = [
            p for p in phases if p.execution_mode == ExecutionMode.PARALLEL_SAFE
        ]
        if len(parallel_phases) < len(phases) / 2:
            validation_result["optimization_suggestions"].append(
                "Consider optimizing agent profiles for more parallel execution"
            )

        return validation_result

    def get_execution_statistics(self, phases: List[ExecutionPhase]) -> Dict[str, Any]:
        """Get execution plan statistics."""
        total_agents = sum(len(phase.agents) for phase in phases)
        parallel_agents = sum(
            len(phase.agents)
            for phase in phases
            if phase.execution_mode == ExecutionMode.PARALLEL_SAFE
        )

        sequential_duration = sum(
            sum(
                self.agent_profiles[agent].execution_time_estimate
                for agent in phase.agents
                if agent in self.agent_profiles
            )
            for phase in phases
        )

        parallel_duration = sum(phase.estimated_duration for phase in phases)

        efficiency = (
            ((sequential_duration - parallel_duration) / sequential_duration * 100)
            if sequential_duration > 0
            else 0
        )

        return {
            "total_phases": len(phases),
            "total_agents": total_agents,
            "parallel_agents": parallel_agents,
            "parallelization_rate": (
                (parallel_agents / total_agents * 100) if total_agents > 0 else 0
            ),
            "sequential_duration": sequential_duration,
            "parallel_duration": parallel_duration,
            "efficiency_gain": efficiency,
        }
