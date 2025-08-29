"""Tests for intelligent execution planner system."""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict

from src.core.intelligent_execution_planner import (
    IntelligentExecutionPlanner,
    AgentDependency,
    ExecutionPlan,
    ParallelGroup,
    ResourceConflict
)


class TestAgentDependency:
    """Test AgentDependency dataclass."""
    
    def test_agent_dependency_creation(self):
        """Test creating agent dependencies."""
        dependency = AgentDependency(
            agent="modifier",
            depends_on=["analyzer"],
            provides=["code_changes"],
            conflicts_with=["tester"],
            priority=2
        )
        
        assert dependency.agent == "modifier"
        assert dependency.depends_on == ["analyzer"]
        assert dependency.provides == ["code_changes"]
        assert dependency.conflicts_with == ["tester"]
        assert dependency.priority == 2


class TestParallelGroup:
    """Test ParallelGroup dataclass."""
    
    def test_parallel_group_creation(self):
        """Test creating parallel execution groups."""
        group = ParallelGroup(
            agents=["analyzer", "architect"],
            estimated_duration=45.0,
            resource_requirements={"cpu": 2, "memory": 1024}
        )
        
        assert group.agents == ["analyzer", "architect"]
        assert group.estimated_duration == 45.0
        assert group.resource_requirements == {"cpu": 2, "memory": 1024}


class TestResourceConflict:
    """Test ResourceConflict dataclass."""
    
    def test_resource_conflict_creation(self):
        """Test creating resource conflicts."""
        conflict = ResourceConflict(
            agent1="modifier",
            agent2="tester",
            resource="file_system",
            severity="high",
            resolution="sequential"
        )
        
        assert conflict.agent1 == "modifier"
        assert conflict.agent2 == "tester"
        assert conflict.resource == "file_system"
        assert conflict.severity == "high"
        assert conflict.resolution == "sequential"


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""
    
    def test_execution_plan_creation(self):
        """Test creating execution plans."""
        group1 = ParallelGroup(agents=["analyzer"], estimated_duration=30.0)
        group2 = ParallelGroup(agents=["modifier"], estimated_duration=60.0)
        
        conflict = ResourceConflict(
            agent1="modifier", agent2="tester", 
            resource="files", severity="medium", resolution="sequential"
        )
        
        plan = ExecutionPlan(
            parallel_groups=[group1, group2],
            execution_order=["analyzer", "modifier"],
            estimated_total_duration=90.0,
            resource_conflicts=[conflict],
            optimization_applied=True
        )
        
        assert len(plan.parallel_groups) == 2
        assert plan.execution_order == ["analyzer", "modifier"]
        assert plan.estimated_total_duration == 90.0
        assert len(plan.resource_conflicts) == 1
        assert plan.optimization_applied is True


class TestIntelligentExecutionPlanner:
    """Test IntelligentExecutionPlanner functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.planner = IntelligentExecutionPlanner()
    
    def test_initialization(self):
        """Test planner initialization."""
        assert isinstance(self.planner.agent_dependencies, dict)
        assert len(self.planner.agent_dependencies) > 0
        
        # Check that standard agents are defined
        expected_agents = {"analyzer", "architect", "modifier", "tester", "reviewer"}
        assert expected_agents.issubset(set(self.planner.agent_dependencies.keys()))
    
    def test_get_agent_dependencies(self):
        """Test getting agent dependencies."""
        analyzer_deps = self.planner.get_agent_dependencies("analyzer")
        
        assert isinstance(analyzer_deps, AgentDependency)
        assert analyzer_deps.agent == "analyzer"
        assert len(analyzer_deps.depends_on) == 0  # Analyzer has no dependencies
        
        modifier_deps = self.planner.get_agent_dependencies("modifier")
        assert "analyzer" in modifier_deps.depends_on
    
    def test_detect_conflicts(self):
        """Test conflict detection between agents."""
        agents = ["modifier", "tester"]
        conflicts = self.planner.detect_conflicts(agents)
        
        assert isinstance(conflicts, list)
        # modifier and tester conflict on file system access
        conflict_agents = set()
        for conflict in conflicts:
            conflict_agents.add(conflict.agent1)
            conflict_agents.add(conflict.agent2)
        
        if len(conflicts) > 0:
            assert "modifier" in conflict_agents or "tester" in conflict_agents
    
    def test_topological_sort_simple(self):
        """Test topological sorting with simple dependencies."""
        agents = ["analyzer", "modifier"]
        sorted_agents = self.planner.topological_sort(agents)
        
        # analyzer should come before modifier
        analyzer_index = sorted_agents.index("analyzer")
        modifier_index = sorted_agents.index("modifier")
        assert analyzer_index < modifier_index
    
    def test_topological_sort_complex(self):
        """Test topological sorting with complex dependencies."""
        agents = ["reviewer", "tester", "modifier", "analyzer"]
        sorted_agents = self.planner.topological_sort(agents)
        
        # Check that dependencies are respected
        analyzer_index = sorted_agents.index("analyzer")
        modifier_index = sorted_agents.index("modifier")
        tester_index = sorted_agents.index("tester")
        reviewer_index = sorted_agents.index("reviewer")
        
        # analyzer should come before modifier
        assert analyzer_index < modifier_index
        # modifier should come before tester
        assert modifier_index < tester_index
        # tester should come before reviewer
        assert tester_index < reviewer_index
    
    def test_topological_sort_invalid_agent(self):
        """Test topological sorting with invalid agent."""
        agents = ["analyzer", "invalid_agent"]
        sorted_agents = self.planner.topological_sort(agents)
        
        # Should handle invalid agents gracefully
        assert "analyzer" in sorted_agents
        assert "invalid_agent" in sorted_agents
    
    def test_optimize_parallel_execution_simple(self):
        """Test parallel execution optimization."""
        agents = ["analyzer", "architect"]  # These can run in parallel
        groups = self.planner.optimize_parallel_execution(agents)
        
        assert isinstance(groups, list)
        assert len(groups) >= 1
        
        # Check that all agents are included
        all_agents = []
        for group in groups:
            all_agents.extend(group.agents)
        assert set(all_agents) == set(agents)
    
    def test_optimize_parallel_execution_with_dependencies(self):
        """Test parallel execution with dependencies."""
        agents = ["analyzer", "modifier", "architect"]
        groups = self.planner.optimize_parallel_execution(agents)
        
        # analyzer and architect can run in parallel
        # modifier must run after analyzer
        all_agents = []
        for group in groups:
            all_agents.extend(group.agents)
        assert set(all_agents) == set(agents)
        
        # Verify dependency order
        group_positions = {}
        for i, group in enumerate(groups):
            for agent in group.agents:
                group_positions[agent] = i
        
        # analyzer should be in an earlier or same group as modifier
        if "analyzer" in group_positions and "modifier" in group_positions:
            assert group_positions["analyzer"] <= group_positions["modifier"]
    
    def test_estimate_execution_time(self):
        """Test execution time estimation."""
        agents = ["analyzer", "modifier"]
        duration = self.planner.estimate_execution_time(agents, "medium", "low")
        
        assert isinstance(duration, float)
        assert duration > 0
        
        # Higher complexity should take longer
        high_duration = self.planner.estimate_execution_time(agents, "high", "critical")
        assert high_duration >= duration
    
    def test_create_execution_plan_simple(self):
        """Test creating execution plan."""
        agents = ["analyzer"]
        plan = self.planner.create_execution_plan(
            agents=agents,
            task_description="Simple analysis task",
            complexity="low",
            risk_level="low"
        )
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.parallel_groups) >= 1
        assert plan.execution_order == agents
        assert plan.estimated_total_duration > 0
    
    def test_create_execution_plan_complex(self):
        """Test creating complex execution plan."""
        agents = ["analyzer", "modifier", "tester", "reviewer"]
        plan = self.planner.create_execution_plan(
            agents=agents,
            task_description="Complex development task",
            complexity="high",
            risk_level="critical"
        )
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.parallel_groups) >= 1
        assert len(plan.execution_order) == len(agents)
        assert plan.estimated_total_duration > 0
        
        # Verify dependency order is maintained
        execution_positions = {}
        for i, agent in enumerate(plan.execution_order):
            execution_positions[agent] = i
        
        # Check key dependencies
        if "analyzer" in execution_positions and "modifier" in execution_positions:
            assert execution_positions["analyzer"] < execution_positions["modifier"]
        
        if "modifier" in execution_positions and "tester" in execution_positions:
            assert execution_positions["modifier"] < execution_positions["tester"]
    
    def test_create_execution_plan_with_conflicts(self):
        """Test creating execution plan with resource conflicts."""
        agents = ["modifier", "tester"]  # These conflict on file system
        plan = self.planner.create_execution_plan(
            agents=agents,
            task_description="Task with conflicts",
            complexity="medium",
            risk_level="medium"
        )
        
        assert isinstance(plan, ExecutionPlan)
        # Should handle conflicts by making them sequential
        assert len(plan.parallel_groups) >= 1
        
        # Check if conflicts were detected and handled
        if len(plan.resource_conflicts) > 0:
            conflict = plan.resource_conflicts[0]
            assert conflict.resolution in ["sequential", "resource_isolation"]


class TestExecutionPlannerEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Setup test environment."""
        self.planner = IntelligentExecutionPlanner()
    
    def test_empty_agent_list(self):
        """Test with empty agent list."""
        plan = self.planner.create_execution_plan(
            agents=[],
            task_description="Empty task",
            complexity="low",
            risk_level="low"
        )
        
        assert len(plan.parallel_groups) == 0
        assert len(plan.execution_order) == 0
        assert plan.estimated_total_duration == 0
    
    def test_single_agent(self):
        """Test with single agent."""
        plan = self.planner.create_execution_plan(
            agents=["analyzer"],
            task_description="Single agent task",
            complexity="medium",
            risk_level="low"
        )
        
        assert len(plan.parallel_groups) == 1
        assert plan.parallel_groups[0].agents == ["analyzer"]
        assert plan.execution_order == ["analyzer"]
    
    def test_unknown_agents(self):
        """Test with unknown agent types."""
        agents = ["unknown_agent1", "unknown_agent2"]
        plan = self.planner.create_execution_plan(
            agents=agents,
            task_description="Unknown agents task",
            complexity="low",
            risk_level="low"
        )
        
        # Should handle unknown agents gracefully
        assert len(plan.parallel_groups) >= 1
        all_agents = []
        for group in plan.parallel_groups:
            all_agents.extend(group.agents)
        assert set(all_agents) == set(agents)
    
    def test_mixed_known_unknown_agents(self):
        """Test with mix of known and unknown agents."""
        agents = ["analyzer", "unknown_agent", "modifier"]
        plan = self.planner.create_execution_plan(
            agents=agents,
            task_description="Mixed agents task",
            complexity="medium",
            risk_level="low"
        )
        
        assert len(plan.parallel_groups) >= 1
        all_agents = []
        for group in plan.parallel_groups:
            all_agents.extend(group.agents)
        assert set(all_agents) == set(agents)
        
        # Known dependencies should still be respected
        execution_positions = {}
        for i, agent in enumerate(plan.execution_order):
            execution_positions[agent] = i
        
        if "analyzer" in execution_positions and "modifier" in execution_positions:
            assert execution_positions["analyzer"] < execution_positions["modifier"]


class TestExecutionPlannerIntegration:
    """Integration tests for execution planner."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from agents to execution plan."""
        planner = IntelligentExecutionPlanner()
        
        # Full development workflow
        agents = ["analyzer", "architect", "modifier", "tester", "reviewer"]
        
        plan = planner.create_execution_plan(
            agents=agents,
            task_description="Complete development workflow",
            complexity="high",
            risk_level="medium"
        )
        
        # Verify plan completeness
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.parallel_groups) >= 1
        assert len(plan.execution_order) == len(agents)
        assert plan.estimated_total_duration > 0
        
        # Verify all agents are included
        all_agents = []
        for group in plan.parallel_groups:
            all_agents.extend(group.agents)
        assert set(all_agents) == set(agents)
        
        # Verify execution order respects dependencies
        execution_positions = {}
        for i, agent in enumerate(plan.execution_order):
            execution_positions[agent] = i
        
        # Key dependency checks
        assert execution_positions["analyzer"] < execution_positions["modifier"]
        assert execution_positions["modifier"] < execution_positions["tester"]
        assert execution_positions["tester"] < execution_positions["reviewer"]
    
    def test_performance_with_large_agent_set(self):
        """Test performance with many agents."""
        planner = IntelligentExecutionPlanner()
        
        # Large set of agents including duplicates and unknowns
        agents = [
            "analyzer", "architect", "modifier", "tester", "reviewer",
            "analyzer", "security_agent", "performance_agent", 
            "documentation_agent", "deployment_agent"
        ]
        
        import time
        start_time = time.time()
        
        plan = planner.create_execution_plan(
            agents=agents,
            task_description="Large scale task",
            complexity="high",
            risk_level="critical"
        )
        
        duration = time.time() - start_time
        
        # Should complete quickly (under 1 second)
        assert duration < 1.0
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.parallel_groups) >= 1


if __name__ == "__main__":
    pytest.main([__file__])