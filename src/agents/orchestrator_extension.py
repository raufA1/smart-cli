"""Orchestrator extension methods for parallel execution."""

import asyncio
import time
from typing import Dict, List, Any

async def _execute_parallel_pipeline(
    self, execution_plan, original_request: str, phase_mapping: Dict, 
    complexity: str, risk: str
) -> List[Any]:
    """Execute agents in parallel groups according to execution plan."""
    results = []
    
    for group_index, group in enumerate(execution_plan.parallel_groups):
        self.ui.add_event("🔄", "System", f"Executing parallel group {group_index + 1}")
        
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
        
        # Check if we should continue to next group
        if risk in ["critical", "high"]:
            failures = [r for r in group_results if isinstance(r, Exception) or not getattr(r, 'success', True)]
            if failures:
                self.ui.add_event("🛑", "System", "Critical failure in parallel group", "error")
                break
    
    return results

async def _execute_single_agent(
    self, agent_type: str, phase_name: str, original_request: str, 
    complexity: str, risk: str
):
    """Execute a single agent with UI updates."""
    # Start phase and agent
    self.ui.start_phase(phase_name)
    task_desc = self._get_agent_task_description(agent_type)
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