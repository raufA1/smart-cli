"""Multi-agent workflow orchestration system."""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from .ai_client import OpenRouterClient, ChatMessage, AIResponse
from .config import ConfigManager


class AgentRole(Enum):
    """Available agent roles."""
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    DEBUGGER = "debugger"
    REFACTOR_SPECIALIST = "refactor_specialist"
    DOCUMENTATION = "documentation"
    TEST_GENERATOR = "test_generator"
    SECURITY_AUDITOR = "security_auditor"


@dataclass
class AgentTask:
    """Task for agent processing."""
    task_id: str
    agent_role: AgentRole
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 = high, 5 = low
    created_at: datetime = field(default_factory=datetime.now)
    

@dataclass
class AgentResult:
    """Result from agent processing."""
    task_id: str
    agent_role: AgentRole
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)


class Agent(ABC):
    """Base agent class."""
    
    def __init__(self, role: AgentRole, ai_client: OpenRouterClient):
        self.role = role
        self.ai_client = ai_client
        self.logger = structlog.get_logger()
        
        # Performance metrics
        self.performance_metrics = {
            'tasks_completed': 0,
            'total_execution_time': 0.0,
            'success_rate': 0.0,
            'average_quality_score': 0.0,
            'total_tokens_used': 0,
            'total_cost': 0.0,
        }
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process a task and return result."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent."""
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return self.performance_metrics.copy()
    
    def update_metrics(self, result: AgentResult):
        """Update performance metrics based on result."""
        self.performance_metrics['tasks_completed'] += 1
        self.performance_metrics['total_execution_time'] += result.execution_time
        self.performance_metrics['total_tokens_used'] += result.tokens_used
        self.performance_metrics['total_cost'] += result.cost_estimate
        
        if result.success:
            success_count = self.performance_metrics.get('successful_tasks', 0) + 1
            self.performance_metrics['successful_tasks'] = success_count
            
        total_tasks = self.performance_metrics['tasks_completed']
        successful_tasks = self.performance_metrics.get('successful_tasks', 0)
        self.performance_metrics['success_rate'] = successful_tasks / total_tasks if total_tasks > 0 else 0


class CodeGeneratorAgent(Agent):
    """Agent specialized in code generation."""
    
    def __init__(self, ai_client: OpenRouterClient):
        super().__init__(AgentRole.CODE_GENERATOR, ai_client)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for code generation."""
        return """You are a senior software engineer specialized in code generation.

Your responsibilities:
- Generate clean, efficient, and well-documented code
- Follow language-specific best practices and conventions
- Include comprehensive error handling
- Write code that is maintainable and testable
- Provide inline comments and documentation

Always:
- Ask clarifying questions if requirements are unclear
- Suggest improvements to requirements when appropriate
- Include unit tests when generating functions/classes
- Follow SOLID principles and design patterns
- Consider security implications in your code

Output format:
- Provide complete, runnable code
- Include installation/setup instructions if needed
- Add usage examples
- Explain key design decisions
"""
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Generate code based on task requirements."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare messages for AI
            messages = [
                ChatMessage(role="system", content=self.get_system_prompt()),
                ChatMessage(role="user", content=self._build_generation_prompt(task))
            ]
            
            # Generate response
            ai_response = await self.ai_client.generate_response(messages)
            
            # Create result
            result = AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                success=True,
                content=ai_response.content,
                metadata={
                    'model_used': ai_response.model,
                    'language': task.context.get('language', 'python'),
                    'function_name': task.context.get('function_name'),
                    'class_name': task.context.get('class_name'),
                },
                execution_time=asyncio.get_event_loop().time() - start_time,
                tokens_used=ai_response.usage.get('total_tokens', 0),
                cost_estimate=ai_response.cost_estimate or 0.0,
            )
            
            self.update_metrics(result)
            return result
            
        except Exception as e:
            self.logger.error("Code generation failed", error=str(e), task_id=task.task_id)
            
            result = AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                success=False,
                content=f"Code generation failed: {str(e)}",
                execution_time=asyncio.get_event_loop().time() - start_time,
            )
            
            self.update_metrics(result)
            return result
    
    def _build_generation_prompt(self, task: AgentTask) -> str:
        """Build generation prompt from task context."""
        language = task.context.get('language', 'python')
        requirements = task.description
        
        prompt = f"""
Generate {language} code for the following requirements:

{requirements}

Context:
"""
        
        if task.context.get('function_name'):
            prompt += f"- Function name: {task.context['function_name']}\n"
        
        if task.context.get('class_name'):
            prompt += f"- Class name: {task.context['class_name']}\n"
        
        if task.context.get('framework'):
            prompt += f"- Framework: {task.context['framework']}\n"
        
        if task.context.get('additional_requirements'):
            prompt += f"- Additional requirements: {task.context['additional_requirements']}\n"
        
        prompt += """
Please provide:
1. Complete, working code with proper error handling
2. Comprehensive documentation and comments
3. Unit tests for the generated code
4. Usage examples
5. Any necessary dependencies or setup instructions

Make sure the code follows best practices and is production-ready.
"""
        
        return prompt


class CodeReviewerAgent(Agent):
    """Agent specialized in code review."""
    
    def __init__(self, ai_client: OpenRouterClient):
        super().__init__(AgentRole.CODE_REVIEWER, ai_client)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for code review."""
        return """You are a senior software engineer specialized in code review.

Your responsibilities:
- Analyze code for bugs, security vulnerabilities, and performance issues
- Check adherence to coding standards and best practices
- Suggest improvements and refactoring opportunities
- Identify potential maintenance and scalability issues
- Verify test coverage and quality

Focus areas:
- Code quality and readability
- Security vulnerabilities (OWASP Top 10)
- Performance bottlenecks
- Memory leaks and resource management
- Error handling and edge cases
- Documentation completeness
- Test coverage

Output a structured review with:
1. Overall assessment (score out of 10)
2. Critical issues (must fix)
3. Major issues (should fix)
4. Minor issues (nice to fix)
5. Positive aspects
6. Recommendations for improvement
"""
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Review code based on task requirements."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            messages = [
                ChatMessage(role="system", content=self.get_system_prompt()),
                ChatMessage(role="user", content=self._build_review_prompt(task))
            ]
            
            ai_response = await self.ai_client.generate_response(messages)
            
            result = AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                success=True,
                content=ai_response.content,
                metadata={
                    'model_used': ai_response.model,
                    'language': task.context.get('language', 'unknown'),
                    'review_focus': task.context.get('focus', 'general'),
                    'file_path': task.context.get('file_path'),
                },
                execution_time=asyncio.get_event_loop().time() - start_time,
                tokens_used=ai_response.usage.get('total_tokens', 0),
                cost_estimate=ai_response.cost_estimate or 0.0,
            )
            
            self.update_metrics(result)
            return result
            
        except Exception as e:
            self.logger.error("Code review failed", error=str(e), task_id=task.task_id)
            
            result = AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                success=False,
                content=f"Code review failed: {str(e)}",
                execution_time=asyncio.get_event_loop().time() - start_time,
            )
            
            self.update_metrics(result)
            return result
    
    def _build_review_prompt(self, task: AgentTask) -> str:
        """Build review prompt from task context."""
        code = task.context.get('code', '')
        language = task.context.get('language', 'unknown')
        focus = task.context.get('focus', 'general')
        file_path = task.context.get('file_path', 'unknown')
        
        return f"""
Please review the following {language} code from file: {file_path}

Review focus: {focus}

Code to review:
```{language}
{code}
```

Additional context:
{task.description}

Please provide a comprehensive review following the structured format specified in your system prompt.
"""


class MultiAgentWorkflow:
    """Orchestrates multiple agents to complete complex workflows."""
    
    def __init__(self, ai_client: OpenRouterClient):
        self.ai_client = ai_client
        self.agents: Dict[AgentRole, Agent] = {}
        self.task_queue = asyncio.Queue()
        self.results: Dict[str, AgentResult] = {}
        self.logger = structlog.get_logger()
        
        # Initialize default agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize available agents."""
        self.agents[AgentRole.CODE_GENERATOR] = CodeGeneratorAgent(self.ai_client)
        self.agents[AgentRole.CODE_REVIEWER] = CodeReviewerAgent(self.ai_client)
        # Add more agents as needed
    
    def register_agent(self, agent: Agent):
        """Register a custom agent."""
        self.agents[agent.role] = agent
    
    async def execute_workflow(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """Execute a workflow with multiple tasks."""
        self.logger.info("Starting workflow execution", task_count=len(tasks))
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        
        # Execute tasks
        results = {}
        
        for task in sorted_tasks:
            if task.agent_role not in self.agents:
                self.logger.error("Agent not available", role=task.agent_role.value)
                results[task.task_id] = AgentResult(
                    task_id=task.task_id,
                    agent_role=task.agent_role,
                    success=False,
                    content=f"Agent {task.agent_role.value} not available",
                )
                continue
            
            agent = self.agents[task.agent_role]
            
            try:
                self.logger.info("Processing task", task_id=task.task_id, agent=task.agent_role.value)
                result = await agent.process_task(task)
                results[task.task_id] = result
                
                self.logger.info(
                    "Task completed",
                    task_id=task.task_id,
                    success=result.success,
                    execution_time=result.execution_time
                )
                
            except Exception as e:
                self.logger.error("Task execution failed", task_id=task.task_id, error=str(e))
                results[task.task_id] = AgentResult(
                    task_id=task.task_id,
                    agent_role=task.agent_role,
                    success=False,
                    content=f"Task execution failed: {str(e)}",
                )
        
        self.results.update(results)
        self.logger.info("Workflow execution completed", total_tasks=len(tasks))
        
        return results
    
    async def execute_parallel_workflow(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """Execute tasks in parallel where possible."""
        self.logger.info("Starting parallel workflow execution", task_count=len(tasks))
        
        # Group tasks by agent type to avoid conflicts
        agent_tasks: Dict[AgentRole, List[AgentTask]] = {}
        for task in tasks:
            if task.agent_role not in agent_tasks:
                agent_tasks[task.agent_role] = []
            agent_tasks[task.agent_role].append(task)
        
        # Execute each agent's tasks concurrently
        all_results = {}
        agent_coroutines = []
        
        for agent_role, agent_task_list in agent_tasks.items():
            if agent_role in self.agents:
                coroutine = self._execute_agent_tasks(agent_role, agent_task_list)
                agent_coroutines.append(coroutine)
        
        # Wait for all agents to complete
        agent_results = await asyncio.gather(*agent_coroutines, return_exceptions=True)
        
        # Collect results
        for result in agent_results:
            if isinstance(result, dict):
                all_results.update(result)
            elif isinstance(result, Exception):
                self.logger.error("Agent execution failed", error=str(result))
        
        self.results.update(all_results)
        self.logger.info("Parallel workflow execution completed", total_tasks=len(tasks))
        
        return all_results
    
    async def _execute_agent_tasks(self, agent_role: AgentRole, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """Execute all tasks for a specific agent."""
        agent = self.agents[agent_role]
        results = {}
        
        for task in tasks:
            try:
                result = await agent.process_task(task)
                results[task.task_id] = result
            except Exception as e:
                self.logger.error("Agent task failed", agent=agent_role.value, task_id=task.task_id, error=str(e))
                results[task.task_id] = AgentResult(
                    task_id=task.task_id,
                    agent_role=agent_role,
                    success=False,
                    content=f"Agent task failed: {str(e)}",
                )
        
        return results
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of workflow execution."""
        total_tasks = len(self.results)
        successful_tasks = sum(1 for r in self.results.values() if r.success)
        total_execution_time = sum(r.execution_time for r in self.results.values())
        total_tokens = sum(r.tokens_used for r in self.results.values())
        total_cost = sum(r.cost_estimate for r in self.results.values())
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': successful_tasks / total_tasks if total_tasks > 0 else 0,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / total_tasks if total_tasks > 0 else 0,
            'total_tokens_used': total_tokens,
            'total_estimated_cost': total_cost,
            'agents_used': list(set(r.agent_role.value for r in self.results.values())),
        }
    
    def get_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all agents."""
        return {
            role.value: agent.get_performance_metrics()
            for role, agent in self.agents.items()
        }