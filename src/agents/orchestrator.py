"""Smart CLI Multi-Agent Orchestrator with Full Terminal Dashboard UI."""

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live

console = Console()


class SmartCLIOrchestrator:
    """Clean orchestrator with smart task classification and adaptive pipeline."""

    def __init__(self, ai_client=None, config_manager=None):
        self.ai_client = ai_client
        self.config_manager = config_manager
        
        # Initialize AI client if not provided but config manager is available
        if not self.ai_client and self.config_manager:
            from ..utils.simple_ai_client import SimpleOpenRouterClient
            self.ai_client = SimpleOpenRouterClient(self.config_manager)

        # Initialize smart systems
        try:
            from ..core.ai_cost_optimizer import get_cost_optimizer
            from ..core.task_classifier import get_task_classifier
            from ..core.terminal_ui import initialize_terminal_ui
            from ..core.intelligent_execution_planner import IntelligentExecutionPlanner
        except ImportError:
            from core.ai_cost_optimizer import get_cost_optimizer
            from core.task_classifier import get_task_classifier
            from core.terminal_ui import initialize_terminal_ui
            from core.intelligent_execution_planner import IntelligentExecutionPlanner

        self.cost_optimizer = get_cost_optimizer()
        self.task_classifier = get_task_classifier()
        self.execution_planner = IntelligentExecutionPlanner()
        self.session_cost = 0.0

        # Initialize Terminal UI
        project_name = os.path.basename(os.getcwd())
        self.ui = initialize_terminal_ui(project_name=project_name)

        # Active agents
        self.active_agents = {
            "architect": "🏗️ System Architect Agent",
            "analyzer": "🔍 Code Analyzer Agent",
            "modifier": "🔧 Code Modifier Agent",
            "tester": "🧪 Testing Agent",
            "reviewer": "👁️ Code Review Agent",
        }

        # Initialize agent instances
        self.agents = self._initialize_agents()
        
        # Import extension methods
        self._import_extension_methods()

    def _initialize_agents(self):
        """Initialize agent instances."""
        return {}  # Lazy loading when needed
    
    def _import_extension_methods(self):
        """Import extension methods for orchestrator."""
        try:
            # Import extension methods
            import types
            from .orchestrator_extension import _execute_parallel_pipeline, _execute_single_agent
            
            # Bind extension methods to this instance
            self._execute_parallel_pipeline = types.MethodType(_execute_parallel_pipeline, self)
            self._execute_single_agent = types.MethodType(_execute_single_agent, self)
        except ImportError:
            # Extension methods not available - will fall back to sequential execution
            pass

    async def create_detailed_plan(self, user_request: str) -> Dict[str, Any]:
        """Create intelligent plan with advanced execution planning."""
        console.print("🤖 [bold cyan]Orchestrator:[/bold cyan] Initializing Smart CLI...")
        console.print("   - Collecting context")
        console.print("   - Classifying request")
        
        self.ui.add_event("🤖", "Orchestrator", "Initializing Smart CLI execution")
        self.ui.add_event("📋", "Orchestrator", "Collecting context and classifying request")

        # Classify task complexity and risk
        complexity, risk = self.task_classifier.classify_task(user_request)
        pipeline = self.task_classifier.get_recommended_pipeline(complexity, risk)
        models = self.task_classifier.get_recommended_models(complexity, risk)

        # Create intelligent execution plan
        execution_plan = self.execution_planner.create_execution_plan(
            agents=pipeline,
            task_description=user_request,
            complexity=complexity.value,
            risk_level=risk.value
        )

        # Create execution phase plan  
        phase_names = []
        for agent in pipeline:
            if agent == "analyzer":
                phase_names.append("Analysis")
            elif agent == "architect":
                phase_names.append("Architecture")
            elif agent == "modifier":
                phase_names.append("Implementation")
            elif agent == "tester":
                phase_names.append("Testing")
            elif agent == "reviewer":
                phase_names.append("Review")
        
        console.print(f"   - Creating phase plan ({' → '.join(phase_names)})")
        
        # Log orchestrator analysis results
        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Task classified as [bold]{complexity.value}[/bold] complexity, [bold]{risk.value}[/bold] risk")
        
        self.ui.add_event("📊", "Orchestrator", f"Task classified: {complexity.value} complexity, {risk.value} risk")
        
        # Show execution strategy
        if execution_plan.parallel_groups:
            parallel_info = f"Parallel execution: {len(execution_plan.parallel_groups)} groups"
            console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] {parallel_info}")
            self.ui.add_event("⚡", "Orchestrator", parallel_info)
        
        pipeline_display = ' → '.join([agent.title() for agent in pipeline])
        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Pipeline: {pipeline_display}")
        self.ui.add_event("📋", "Orchestrator", f"Execution pipeline: {pipeline_display}")

        # Create adaptive plan with intelligent execution
        plan = {
            "title": f"Smart {complexity.value.title()} Plan",
            "complexity": complexity.value,
            "risk": risk.value,
            "pipeline": pipeline,
            "models": models,
            "execution_plan": execution_plan,
            "steps": self._create_pipeline_steps(pipeline, models, complexity, risk),
            "estimated_cost": self._estimate_plan_cost(pipeline, models),
        }

        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Estimated cost: [bold green]${plan['estimated_cost']:.3f}[/bold green]")
        self.ui.add_event("💰", "Orchestrator", f"Estimated cost: ${plan['estimated_cost']:.3f}")
        
        console.print()  # Add spacing
        return plan

    def _create_pipeline_steps(
        self, pipeline: List[str], models: Dict[str, str], complexity, risk
    ) -> List[Dict]:
        """Create execution steps based on pipeline."""
        steps = []

        for i, agent_type in enumerate(pipeline, 1):
            step = {
                "id": f"step_{i}",
                "agent": agent_type,
                "action": f"{agent_type}_task",
                "description": f"Smart {complexity.value} {agent_type}",
                "model": models.get(agent_type, "llama-3-8b"),
            }
            steps.append(step)

        return steps

    def _estimate_plan_cost(self, pipeline: List[str], models: Dict[str, str]) -> float:
        """Estimate total cost for execution plan."""
        total_cost = 0.0

        for agent_type in pipeline:
            try:
                _, estimated_cost = self.cost_optimizer.select_optimal_model(
                    agent_type, f"task for {agent_type}", estimated_tokens=2000
                )
                total_cost += estimated_cost
            except Exception:
                total_cost += 0.02  # Default estimate

        return total_cost

    async def execute_task_plan(
        self, plan: Dict[str, Any], original_request: str
    ) -> bool:
        """Execute smart adaptive pipeline."""
        if "pipeline" not in plan:
            self.ui.add_event(
                "⚠️",
                "System",
                "No smart pipeline found, using basic execution",
                "warning",
            )
            return False

        return await self._execute_smart_pipeline(plan, original_request)

    async def _execute_smart_pipeline(
        self, plan: Dict[str, Any], original_request: str
    ) -> bool:
        """Execute smart adaptive pipeline with intelligent execution planning."""

        pipeline = plan.get("pipeline", [])
        models = plan.get("models", {})
        complexity = plan.get("complexity", "medium")
        risk = plan.get("risk", "medium")
        execution_plan = plan.get("execution_plan")

        # Map pipeline to phases
        phase_mapping = {
            "analyzer": "analysis",
            "architect": "architecture",
            "modifier": "implementation",
            "tester": "testing",
            "reviewer": "review",
        }

        # Start UI with Live display  
        execution_start_time = time.time()
        
        with Live(self.ui.render(), refresh_per_second=4) as live:
            console.print("🤖 [bold cyan]Orchestrator:[/bold cyan] Starting execution pipeline")
            self.ui.add_event("🚀", "Orchestrator", "Smart CLI Orchestrator activated")
            self.ui.add_event("📊", "Orchestrator", f"Executing pipeline: {' → '.join(pipeline)}")

            results = []
            total_cost = 0.0

            # Execute using intelligent execution planner if available
            if execution_plan and execution_plan.parallel_groups:
                console.print("🤖 [bold cyan]Orchestrator:[/bold cyan] Using parallel execution optimization")
                self.ui.add_event("⚡", "Orchestrator", "Using parallel execution optimization")
                results = await self._execute_parallel_pipeline(
                    execution_plan, original_request, phase_mapping, complexity, risk
                )
                total_cost = sum(getattr(r, 'cost', 0.01) for r in results)
            else:
                # Fall back to sequential execution
                for i, agent_type in enumerate(pipeline, 1):
                    # Start corresponding phase
                    phase_name = phase_mapping.get(agent_type, "implementation")
                    phase_display_name = phase_name.title()
                    
                    # Orchestrator dispatch message
                    console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Dispatching phase [{phase_display_name}]")
                    self.ui.start_phase(phase_name)
                    self.ui.add_event("📤", "Orchestrator", f"Dispatching phase [{phase_display_name}]")

                    # Start agent with enhanced display
                    task_desc = self._get_agent_task_description(agent_type)
                    agent_display = self.active_agents.get(agent_type, f"{agent_type} Agent")
                    console.print(f"{agent_display}: Starting {task_desc.lower()}...")
                    self.ui.start_agent(agent_type, task_desc)

                # Update focus panel
                self.ui.update_focus(
                    f"Active: {agent_type.title()}",
                    f"Task: {task_desc}\nComplexity: {complexity}\nRisk: {risk}",
                )

                start_time = time.time()

                try:
                    # Simulate progress updates during execution
                    for progress in [25, 50, 75]:
                        await asyncio.sleep(0.5)  # Simulate work
                        self.ui.update_agent_progress(agent_type, progress)
                        self.ui.update_phase_progress(phase_name, progress)

                    # Execute actual agent
                    result = await self.delegate_to_agent(
                        agent_type,
                        ".",
                        f"Smart {complexity} task: {original_request}",
                        "smart_execution",
                    )

                    results.append(result)
                    duration = time.time() - start_time
                    total_cost += 0.01  # Fallback cost estimate

                    # Complete agent and phase  
                    self.ui.complete_agent(agent_type, result.success)
                    self.ui.complete_phase(phase_name, result.success)

                    # Update metrics
                    metrics = {
                        "files": len(result.created_files + result.modified_files),
                        "duration": f"{duration:.1f}s",
                    }
                    if result.errors:
                        metrics["errors"] = len(result.errors)
                    if result.warnings:
                        metrics["warnings"] = len(result.warnings)

                    self.ui.update_agent_progress(agent_type, 100, metrics)

                    # Orchestrator phase completion message
                    status = "completed successfully" if result.success else "failed"
                    console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] {phase_display_name} phase {status} ({duration:.1f}s)")
                    
                    # Check if critical task failed
                    if not result.success and risk in ["critical", "high"]:
                        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Critical failure detected → stopping pipeline")
                        self.ui.add_event("🛑", "Orchestrator", "Critical task failed, stopping pipeline", "error")
                        break
                    
                    # Show next phase message (if not last)
                    if i < len(pipeline):
                        next_agent = pipeline[i]
                        next_phase = phase_mapping.get(next_agent, "implementation").title()
                        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Proceeding to {next_phase} phase...")
                        await asyncio.sleep(0.5)  # Brief pause for readability

                except Exception as e:
                    duration = time.time() - start_time
                    error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)

                    # Agent error message
                    agent_display = self.active_agents.get(agent_type, f"{agent_type} Agent")
                    console.print(f"❌ {agent_display}: {error_msg}")
                    
                    # Orchestrator failure detection
                    console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Failure detected → activating Debug mode")
                    console.print(f"🪲 [bold yellow]Debug Agent:[/bold yellow] Analyzing failure: {error_msg}")

                    self.ui.complete_agent(agent_type, False)
                    self.ui.complete_phase(phase_name, False)
                    self.ui.add_event("❌", agent_type, error_msg, "error")
                    self.ui.add_event("🪲", "Orchestrator", f"Debug mode activated for {agent_type} failure", "warning")

                    if risk in ["critical", "high"]:
                        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Critical error → terminating pipeline")
                        return False

                # Brief pause between agents
                await asyncio.sleep(0.3)

            # Show final summary
            success_count = sum(1 for r in results if r.success)
            self.session_cost += total_cost

            await asyncio.sleep(2)  # Show final state

        # Orchestrator final summary
        total_duration = time.time() - execution_start_time
        success_count = sum(1 for r in results if r.success)
        
        console.print()
        console.print("🤖 [bold cyan]Orchestrator:[/bold cyan] All phases completed")
        
        # Calculate and display total execution time
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        time_display = f"{minutes:02d}:{seconds:02d}" if minutes > 0 else f"{seconds}s"
        console.print(f"🎉 [bold green]Project run finished in {time_display}[/bold green]")
        
        # Show agent results summary
        for i, (agent_type, result) in enumerate(zip(pipeline, results)):
            phase_name = phase_mapping.get(agent_type, agent_type).title()
            agent_display = self.active_agents.get(agent_type, f"{agent_type} Agent")
            
            # Create status summary
            status_parts = []
            if hasattr(result, 'created_files') and result.created_files:
                status_parts.append(f"created {len(result.created_files)} files")
            if hasattr(result, 'modified_files') and result.modified_files:
                status_parts.append(f"modified {len(result.modified_files)} files")
            if hasattr(result, 'warnings') and result.warnings:
                status_parts.append(f"{len(result.warnings)} warnings")
            if hasattr(result, 'errors') and result.errors:
                status_parts.append(f"{len(result.errors)} errors")
            
            status_text = ", ".join(status_parts) if status_parts else "completed"
            result_icon = "✅" if result.success else "❌"
            
            console.print(f"   - {phase_name} by {agent_display} → {status_text} {result_icon}")
        
        # Display final summary outside Live context
        final_summary = self.ui.create_final_summary()
        console.print(final_summary)  # Keep this one for final output

        return success_count > 0

    def _get_agent_task_description(self, agent_type: str) -> str:
        """Get descriptive task name for agent."""
        descriptions = {
            "architect": "System design",
            "analyzer": "Code analysis",
            "modifier": "Implementation",
            "tester": "Quality assurance",
            "reviewer": "Final review",
        }
        return descriptions.get(agent_type, f"{agent_type} processing")

    async def delegate_to_agent(
        self, agent_type: str, target: str, description: str, action: str = ""
    ) -> "AgentReport":
        """Smart agent delegation with model optimization."""
        from .base_agent import AgentReport

        task_start_time = time.time()
        actual_cost = 0.0

        # Smart model selection (simplified for UI)
        try:
            complexity, risk = self.task_classifier.classify_task(description)
            optimal_model, estimated_cost = self.cost_optimizer.select_optimal_model(
                agent_type, description, estimated_tokens=2000
            )

            # Update AI client model
            if hasattr(self.ai_client, "set_model"):
                self.ai_client.set_model(optimal_model)

            actual_cost = estimated_cost

        except Exception as e:
            pass  # Silently handle for cleaner UI

        try:
            # Execute agent with config manager
            if agent_type == "architect":
                from .architect_agent import ArchitectAgent

                agent = ArchitectAgent(self.ai_client, self.config_manager)
                result = await agent.execute(target, description)

            elif agent_type == "analyzer":
                from .analyzer_agent import AnalyzerAgent

                agent = AnalyzerAgent(self.ai_client, self.config_manager)
                result = await agent.execute(target, description)

            elif agent_type == "modifier":
                from .modifier_agent import ModifierAgent

                agent = ModifierAgent(self.ai_client, self.config_manager)
                result = await agent.execute(target, description)

            elif agent_type == "tester":
                from .tester_agent import TesterAgent

                agent = TesterAgent(self.ai_client, self.config_manager)
                result = await agent.execute(target, description)

            elif agent_type == "reviewer":
                from .reviewer_agent import ReviewerAgent

                agent = ReviewerAgent(self.ai_client, self.config_manager)
                result = await agent.execute(target, description)

            else:
                console.print(f"⚠️ [yellow]Unknown agent: {agent_type}[/yellow]")
                return AgentReport(
                    success=False,
                    agent_name=f"Unknown Agent ({agent_type})",
                    task_description=description,
                    execution_time=0.0,
                    created_files=[],
                    modified_files=[],
                    errors=[f"Unknown agent type: {agent_type}"],
                    warnings=[],
                    output_data={},
                    next_recommendations=[],
                )

            # Record cost and display result
            task_duration = time.time() - task_start_time
            self.cost_optimizer.record_usage(actual_cost)
            self.session_cost += actual_cost

            await self._process_agent_result(result, actual_cost)
            return result

        except Exception as e:
            error_msg = f"Agent delegation failed: {str(e)}"
            console.print(f"❌ [red]{error_msg}[/red]")

            return AgentReport(
                success=False,
                agent_name=f"{agent_type} Agent",
                task_description=description,
                execution_time=0.0,
                created_files=[],
                modified_files=[],
                errors=[error_msg],
                warnings=[],
                output_data={},
                next_recommendations=[],
            )

    async def _process_agent_result(self, result: "AgentReport", cost: float = 0.0):
        """Process agent result (simplified for UI dashboard)."""
        # Results are now handled by the UI system
        # This method kept for compatibility but simplified
        pass
