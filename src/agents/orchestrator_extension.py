"""Orchestrator extension methods for parallel execution."""

import asyncio
import time
from typing import Dict, List, Any

async def _execute_parallel_pipeline(
    self, execution_plan, original_request: str, phase_mapping: Dict, 
    complexity: str, risk: str
) -> List[Any]:
    """Execute agents in parallel groups according to execution plan."""
    from rich.console import Console
    console = Console()
    
    results = []
    
    for group_index, group in enumerate(execution_plan.parallel_groups):
        group_num = group_index + 1
        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Executing parallel group {group_num}")
        self.ui.add_event("🔄", "Orchestrator", f"Executing parallel group {group_num}")
        
        # Show which agents are running in parallel
        agent_names = [self.active_agents.get(agent, f"{agent} Agent") for agent in group.agents]
        console.print(f"   - Running in parallel: {', '.join(agent_names)}")
        
        # Execute agents in this group concurrently
        group_tasks = []
        for agent_type in group.agents:
            phase_name = phase_mapping.get(agent_type, "implementation")
            task = self._execute_single_agent(
                agent_type, phase_name, original_request, complexity, risk
            )
            group_tasks.append(task)
        
        # Wait for all agents in this group to complete
        group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
        
        # Process results and check for failures
        for result in group_results:
            if isinstance(result, Exception):
                self.ui.add_event("❌", "System", f"Agent failed: {str(result)}", "error")
                # Create error report
                from .base_agent import AgentReport
                error_report = AgentReport(
                    success=False, agent_name="Unknown", task_description=original_request,
                    execution_time=0.0, created_files=[], modified_files=[],
                    errors=[str(result)], warnings=[], output_data={},
                    next_recommendations=[]
                )
                results.append(error_report)
            else:
                results.append(result)
        
        # Orchestrator group completion message
        successful = sum(1 for r in group_results if not isinstance(r, Exception) and getattr(r, 'success', True))
        console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Parallel group {group_num} completed ({successful}/{len(group.agents)} successful)")
        
        # Check if we should continue to next group
        if risk in ["critical", "high"]:
            failures = [r for r in group_results if isinstance(r, Exception) or not getattr(r, 'success', True)]
            if failures:
                console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Critical failure in parallel group → stopping pipeline")
                self.ui.add_event("🛑", "Orchestrator", "Critical failure in parallel group", "error")
                break
    
    return results

async def _execute_single_agent(
    self, agent_type: str, phase_name: str, original_request: str, 
    complexity: str, risk: str
):
    """Execute a single agent with UI updates."""
    from rich.console import Console
    console = Console()
    
    # Orchestrator dispatch for individual agent
    phase_display = phase_name.title()
    console.print(f"🤖 [bold cyan]Orchestrator:[/bold cyan] Dispatching phase [{phase_display}]")
    
    # Start phase and agent
    self.ui.start_phase(phase_name)
    task_desc = self._get_agent_task_description(agent_type)
    
    # Agent start message
    agent_display = self.active_agents.get(agent_type, f"{agent_type} Agent")
    console.print(f"{agent_display}: Starting {task_desc.lower()}...")
    
    self.ui.start_agent(agent_type, task_desc)
    
    start_time = time.time()
    
    try:
        # Simulate progress updates
        for progress in [25, 50, 75]:
            await asyncio.sleep(0.3)
            self.ui.update_agent_progress(agent_type, progress)
            self.ui.update_phase_progress(phase_name, progress)
        
        # Execute actual agent
        result = await self.delegate_to_agent(
            agent_type, ".", f"Smart {complexity} task: {original_request}", "smart_execution"
        )
        
        duration = time.time() - start_time
        
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
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        self.ui.complete_agent(agent_type, False)
        self.ui.complete_phase(phase_name, False)
        self.ui.add_event("❌", agent_type, str(e)[:50], "error")
        raise e