"""Tests for multi-agent system functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid

from src.utils.agents import (
    AgentRole, AgentTask, AgentResult, Agent, 
    CodeGeneratorAgent, CodeReviewerAgent, MultiAgentWorkflow
)
from src.utils.ai_client import OpenRouterClient, ChatMessage, AIResponse


class TestAgentDataClasses:
    """Test agent data classes."""
    
    def test_agent_task_creation(self):
        """Test creating AgentTask."""
        task = AgentTask(
            task_id="test-123",
            agent_role=AgentRole.CODE_GENERATOR,
            description="Generate a function",
            context={"language": "python"},
            priority=1
        )
        
        assert task.task_id == "test-123"
        assert task.agent_role == AgentRole.CODE_GENERATOR
        assert task.description == "Generate a function"
        assert task.context == {"language": "python"}
        assert task.priority == 1
        assert isinstance(task.created_at, datetime)
    
    def test_agent_result_creation(self):
        """Test creating AgentResult."""
        result = AgentResult(
            task_id="test-123",
            agent_role=AgentRole.CODE_GENERATOR,
            success=True,
            content="Generated code",
            metadata={"model": "claude-3"},
            execution_time=1.5,
            tokens_used=100,
            cost_estimate=0.001
        )
        
        assert result.task_id == "test-123"
        assert result.agent_role == AgentRole.CODE_GENERATOR
        assert result.success is True
        assert result.content == "Generated code"
        assert result.metadata == {"model": "claude-3"}
        assert result.execution_time == 1.5
        assert result.tokens_used == 100
        assert result.cost_estimate == 0.001
        assert isinstance(result.completed_at, datetime)


class TestBaseAgent:
    """Test base Agent class."""
    
    class MockAgent(Agent):
        """Mock agent for testing."""
        
        async def process_task(self, task: AgentTask) -> AgentResult:
            """Mock task processing."""
            return AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                success=True,
                content="Mock result",
                execution_time=0.1,
                tokens_used=50,
                cost_estimate=0.0005
            )
        
        def get_system_prompt(self) -> str:
            """Mock system prompt."""
            return "Mock system prompt"
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        return Mock(spec=OpenRouterClient)
    
    @pytest.fixture
    def mock_agent(self, mock_ai_client):
        """Create mock agent."""
        return self.MockAgent(AgentRole.CODE_GENERATOR, mock_ai_client)
    
    def test_agent_initialization(self, mock_agent, mock_ai_client):
        """Test agent initialization."""
        assert mock_agent.role == AgentRole.CODE_GENERATOR
        assert mock_agent.ai_client == mock_ai_client
        assert isinstance(mock_agent.performance_metrics, dict)
        assert mock_agent.performance_metrics['tasks_completed'] == 0
    
    @pytest.mark.asyncio
    async def test_agent_process_task(self, mock_agent):
        """Test agent task processing."""
        task = AgentTask(
            task_id="test-task",
            agent_role=AgentRole.CODE_GENERATOR,
            description="Test task"
        )
        
        result = await mock_agent.process_task(task)
        
        assert isinstance(result, AgentResult)
        assert result.task_id == "test-task"
        assert result.success is True
        assert result.content == "Mock result"
    
    def test_performance_metrics_tracking(self, mock_agent):
        """Test performance metrics tracking."""
        # Initial metrics
        metrics = mock_agent.get_performance_metrics()
        assert metrics['tasks_completed'] == 0
        assert metrics['total_execution_time'] == 0.0
        
        # Update with result
        result = AgentResult(
            task_id="test",
            agent_role=AgentRole.CODE_GENERATOR,
            success=True,
            content="Test",
            execution_time=1.0,
            tokens_used=100,
            cost_estimate=0.01
        )
        
        mock_agent.update_metrics(result)
        
        updated_metrics = mock_agent.get_performance_metrics()
        assert updated_metrics['tasks_completed'] == 1
        assert updated_metrics['total_execution_time'] == 1.0
        assert updated_metrics['total_tokens_used'] == 100
        assert updated_metrics['total_cost'] == 0.01
        assert updated_metrics['successful_tasks'] == 1
        assert updated_metrics['success_rate'] == 1.0
    
    def test_performance_metrics_failed_task(self, mock_agent):
        """Test performance metrics with failed task."""
        result = AgentResult(
            task_id="test",
            agent_role=AgentRole.CODE_GENERATOR,
            success=False,
            content="Error",
            execution_time=0.5,
            tokens_used=20,
            cost_estimate=0.002
        )
        
        mock_agent.update_metrics(result)
        
        metrics = mock_agent.get_performance_metrics()
        assert metrics['tasks_completed'] == 1
        assert metrics['success_rate'] == 0.0  # No successful tasks


class TestCodeGeneratorAgent:
    """Test CodeGeneratorAgent functionality."""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client with response."""
        client = Mock(spec=OpenRouterClient)
        client.generate_response = AsyncMock(return_value=AIResponse(
            content="def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            model="claude-3-sonnet",
            usage={"total_tokens": 150},
            timestamp=datetime.now(),
            cost_estimate=0.003
        ))
        return client
    
    @pytest.fixture
    def generator_agent(self, mock_ai_client):
        """Create CodeGeneratorAgent."""
        return CodeGeneratorAgent(mock_ai_client)
    
    def test_agent_role(self, generator_agent):
        """Test agent role assignment."""
        assert generator_agent.role == AgentRole.CODE_GENERATOR
    
    def test_system_prompt(self, generator_agent):
        """Test system prompt generation."""
        prompt = generator_agent.get_system_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "software engineer" in prompt.lower()
        assert "code generation" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, generator_agent, mock_ai_client):
        """Test successful task processing."""
        task = AgentTask(
            task_id="gen-task-123",
            agent_role=AgentRole.CODE_GENERATOR,
            description="Generate fibonacci function",
            context={
                'language': 'python',
                'function_name': 'fibonacci',
                'type': 'function'
            }
        )
        
        result = await generator_agent.process_task(task)
        
        assert isinstance(result, AgentResult)
        assert result.task_id == "gen-task-123"
        assert result.success is True
        assert "fibonacci" in result.content
        assert result.tokens_used == 150
        assert result.cost_estimate == 0.003
        
        # Check AI client was called correctly
        mock_ai_client.generate_response.assert_called_once()
        call_args = mock_ai_client.generate_response.call_args[0][0]
        assert len(call_args) == 2  # system + user message
        assert call_args[0].role == "system"
        assert call_args[1].role == "user"
    
    @pytest.mark.asyncio
    async def test_process_task_ai_failure(self, mock_ai_client):
        """Test task processing when AI fails."""
        mock_ai_client.generate_response.side_effect = Exception("AI service unavailable")
        generator_agent = CodeGeneratorAgent(mock_ai_client)
        
        task = AgentTask(
            task_id="fail-task",
            agent_role=AgentRole.CODE_GENERATOR,
            description="This will fail"
        )
        
        result = await generator_agent.process_task(task)
        
        assert result.success is False
        assert "AI service unavailable" in result.content
        assert result.execution_time > 0
    
    def test_build_generation_prompt(self, generator_agent):
        """Test prompt building for code generation."""
        task = AgentTask(
            task_id="test",
            agent_role=AgentRole.CODE_GENERATOR,
            description="Create a calculator class",
            context={
                'language': 'python',
                'class_name': 'Calculator',
                'framework': 'FastAPI',
                'additional_requirements': 'Include error handling'
            }
        )
        
        prompt = generator_agent._build_generation_prompt(task)
        
        assert "python" in prompt.lower()
        assert "Create a calculator class" in prompt
        assert "Calculator" in prompt
        assert "FastAPI" in prompt
        assert "error handling" in prompt
        assert "unit tests" in prompt


class TestCodeReviewerAgent:
    """Test CodeReviewerAgent functionality."""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client with review response."""
        client = Mock(spec=OpenRouterClient)
        client.generate_response = AsyncMock(return_value=AIResponse(
            content="## Code Review\n\n**Overall Score: 8/10**\n\n### Issues Found:\n- Minor: Variable naming could be improved",
            model="claude-3-sonnet",
            usage={"total_tokens": 200},
            timestamp=datetime.now(),
            cost_estimate=0.004
        ))
        return client
    
    @pytest.fixture
    def reviewer_agent(self, mock_ai_client):
        """Create CodeReviewerAgent."""
        return CodeReviewerAgent(mock_ai_client)
    
    def test_agent_role(self, reviewer_agent):
        """Test agent role assignment."""
        assert reviewer_agent.role == AgentRole.CODE_REVIEWER
    
    def test_system_prompt(self, reviewer_agent):
        """Test system prompt for code review."""
        prompt = reviewer_agent.get_system_prompt()
        
        assert "code review" in prompt.lower()
        assert "security" in prompt.lower()
        assert "performance" in prompt.lower()
        assert "owasp" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_process_review_task(self, reviewer_agent, mock_ai_client):
        """Test code review task processing."""
        code_to_review = """
def unsafe_function(user_input):
    exec(user_input)  # Security issue!
    return "done"
"""
        
        task = AgentTask(
            task_id="review-task-123",
            agent_role=AgentRole.CODE_REVIEWER,
            description="Review this code for security issues",
            context={
                'code': code_to_review,
                'language': 'python',
                'focus': 'security',
                'file_path': 'unsafe_code.py'
            }
        )
        
        result = await reviewer_agent.process_review_task(task)
        
        assert result.success is True
        assert "Code Review" in result.content
        assert result.tokens_used == 200
        
        # Check the prompt included the code
        mock_ai_client.generate_response.assert_called_once()
        call_args = mock_ai_client.generate_response.call_args[0][0]
        user_message = call_args[1].content
        assert code_to_review in user_message
        assert "security" in user_message
        assert "unsafe_code.py" in user_message
    
    def test_build_review_prompt(self, reviewer_agent):
        """Test review prompt building."""
        task = AgentTask(
            task_id="test",
            agent_role=AgentRole.CODE_REVIEWER,
            description="Security review",
            context={
                'code': 'print("hello")',
                'language': 'python',
                'focus': 'security',
                'file_path': 'test.py'
            }
        )
        
        prompt = reviewer_agent._build_review_prompt(task)
        
        assert 'print("hello")' in prompt
        assert "python" in prompt
        assert "security" in prompt
        assert "test.py" in prompt


class TestMultiAgentWorkflow:
    """Test MultiAgentWorkflow orchestration."""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        return Mock(spec=OpenRouterClient)
    
    @pytest.fixture
    def workflow(self, mock_ai_client):
        """Create MultiAgentWorkflow."""
        return MultiAgentWorkflow(mock_ai_client)
    
    def test_workflow_initialization(self, workflow, mock_ai_client):
        """Test workflow initialization."""
        assert workflow.ai_client == mock_ai_client
        assert AgentRole.CODE_GENERATOR in workflow.agents
        assert AgentRole.CODE_REVIEWER in workflow.agents
        assert isinstance(workflow.agents[AgentRole.CODE_GENERATOR], CodeGeneratorAgent)
        assert isinstance(workflow.agents[AgentRole.CODE_REVIEWER], CodeReviewerAgent)
    
    def test_register_custom_agent(self, workflow, mock_ai_client):
        """Test registering custom agent."""
        class CustomAgent(Agent):
            def __init__(self):
                super().__init__(AgentRole.DEBUGGER, mock_ai_client)
            
            async def process_task(self, task):
                return AgentResult(
                    task_id=task.task_id,
                    agent_role=self.role,
                    success=True,
                    content="Debug result"
                )
            
            def get_system_prompt(self):
                return "Debug system prompt"
        
        custom_agent = CustomAgent()
        workflow.register_agent(custom_agent)
        
        assert AgentRole.DEBUGGER in workflow.agents
        assert workflow.agents[AgentRole.DEBUGGER] == custom_agent
    
    @pytest.mark.asyncio
    async def test_execute_workflow_single_task(self, workflow):
        """Test executing workflow with single task."""
        task = AgentTask(
            task_id="workflow-test-1",
            agent_role=AgentRole.CODE_GENERATOR,
            description="Generate test code"
        )
        
        # Mock the agent processing
        mock_result = AgentResult(
            task_id="workflow-test-1",
            agent_role=AgentRole.CODE_GENERATOR,
            success=True,
            content="Generated test code",
            execution_time=1.0
        )
        
        workflow.agents[AgentRole.CODE_GENERATOR].process_task = AsyncMock(return_value=mock_result)
        
        results = await workflow.execute_workflow([task])
        
        assert len(results) == 1
        assert "workflow-test-1" in results
        assert results["workflow-test-1"] == mock_result
    
    @pytest.mark.asyncio
    async def test_execute_workflow_multiple_tasks(self, workflow):
        """Test executing workflow with multiple tasks."""
        tasks = [
            AgentTask(
                task_id="task-1",
                agent_role=AgentRole.CODE_GENERATOR,
                description="Generate code",
                priority=1
            ),
            AgentTask(
                task_id="task-2",
                agent_role=AgentRole.CODE_REVIEWER,
                description="Review code",
                priority=2
            )
        ]
        
        # Mock both agents
        gen_result = AgentResult(
            task_id="task-1",
            agent_role=AgentRole.CODE_GENERATOR,
            success=True,
            content="Generated code"
        )
        
        review_result = AgentResult(
            task_id="task-2",
            agent_role=AgentRole.CODE_REVIEWER,
            success=True,
            content="Code reviewed"
        )
        
        workflow.agents[AgentRole.CODE_GENERATOR].process_task = AsyncMock(return_value=gen_result)
        workflow.agents[AgentRole.CODE_REVIEWER].process_task = AsyncMock(return_value=review_result)
        
        results = await workflow.execute_workflow(tasks)
        
        assert len(results) == 2
        assert results["task-1"] == gen_result
        assert results["task-2"] == review_result
    
    @pytest.mark.asyncio
    async def test_execute_workflow_unavailable_agent(self, workflow):
        """Test workflow with unavailable agent."""
        task = AgentTask(
            task_id="unavailable-test",
            agent_role=AgentRole.DEBUGGER,  # Not registered by default
            description="Debug task"
        )
        
        results = await workflow.execute_workflow([task])
        
        assert len(results) == 1
        result = results["unavailable-test"]
        assert result.success is False
        assert "Agent debugger not available" in result.content
    
    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, workflow):
        """Test parallel workflow execution."""
        tasks = [
            AgentTask(task_id="parallel-1", agent_role=AgentRole.CODE_GENERATOR, description="Task 1"),
            AgentTask(task_id="parallel-2", agent_role=AgentRole.CODE_GENERATOR, description="Task 2")
        ]
        
        # Mock agent to return different results
        async def mock_process(task):
            return AgentResult(
                task_id=task.task_id,
                agent_role=AgentRole.CODE_GENERATOR,
                success=True,
                content=f"Result for {task.task_id}"
            )
        
        workflow.agents[AgentRole.CODE_GENERATOR].process_task = mock_process
        
        results = await workflow.execute_parallel_workflow(tasks)
        
        assert len(results) == 2
        assert results["parallel-1"].content == "Result for parallel-1"
        assert results["parallel-2"].content == "Result for parallel-2"
    
    def test_workflow_summary_empty(self, workflow):
        """Test workflow summary with no results."""
        summary = workflow.get_workflow_summary()
        
        assert summary['total_tasks'] == 0
        assert summary['successful_tasks'] == 0
        assert summary['success_rate'] == 0
        assert summary['total_execution_time'] == 0
        assert summary['total_tokens_used'] == 0
        assert summary['total_estimated_cost'] == 0
        assert summary['agents_used'] == []
    
    def test_workflow_summary_with_results(self, workflow):
        """Test workflow summary with results."""
        # Simulate some results
        workflow.results = {
            "task-1": AgentResult(
                task_id="task-1",
                agent_role=AgentRole.CODE_GENERATOR,
                success=True,
                content="Success",
                execution_time=1.5,
                tokens_used=100,
                cost_estimate=0.01
            ),
            "task-2": AgentResult(
                task_id="task-2",
                agent_role=AgentRole.CODE_REVIEWER,
                success=False,
                content="Failed",
                execution_time=0.5,
                tokens_used=50,
                cost_estimate=0.005
            )
        }
        
        summary = workflow.get_workflow_summary()
        
        assert summary['total_tasks'] == 2
        assert summary['successful_tasks'] == 1
        assert summary['success_rate'] == 0.5
        assert summary['total_execution_time'] == 2.0
        assert summary['average_execution_time'] == 1.0
        assert summary['total_tokens_used'] == 150
        assert summary['total_estimated_cost'] == 0.015
        assert len(summary['agents_used']) == 2
    
    def test_get_agent_performance(self, workflow):
        """Test getting agent performance metrics."""
        performance = workflow.get_agent_performance()
        
        assert AgentRole.CODE_GENERATOR.value in performance
        assert AgentRole.CODE_REVIEWER.value in performance
        
        # Should include performance metrics structure
        gen_perf = performance[AgentRole.CODE_GENERATOR.value]
        assert 'tasks_completed' in gen_perf
        assert 'success_rate' in gen_perf


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent system."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow from task creation to result."""
        # This would be a comprehensive integration test
        # combining real AI client (mocked), multiple agents, and workflow
        pass