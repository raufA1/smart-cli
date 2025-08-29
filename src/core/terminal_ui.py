"""Smart CLI Terminal UI System - Full dashboard implementation based on UX specification."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

console = Console()


class PhaseStatus(Enum):
    """Phase execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class PhaseInfo:
    """Information about a phase."""

    name: str
    display_name: str
    status: PhaseStatus = PhaseStatus.PENDING
    progress: int = 0
    duration: float = 0.0
    start_time: Optional[float] = None


@dataclass
class AgentInfo:
    """Information about an agent."""

    name: str
    display_name: str
    emoji: str
    status: AgentStatus = AgentStatus.IDLE
    progress: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    current_task: str = ""


@dataclass
class EventInfo:
    """Information about a system event."""

    timestamp: float
    icon: str
    agent: str
    message: str
    level: str = "info"  # info, warning, error


class SmartTerminalUI:
    """Disabled terminal UI to prevent spam."""

    def __init__(self, project_name: str = "unknown", branch: str = "main"):
        # Initialize minimal state to avoid breaking code
        self.project_name = project_name
        self.branch = branch
        self.run_id = f"#{datetime.now().strftime('%Y-%m-%d-%H')}"
        self.start_time = time.time()
        self.layout = None

    # All UI methods disabled to prevent terminal spam
    def setup_layout(self): pass
    def update_header(self, model="", cache=True, concurrency=3, tty=True): pass
    def update_progress(self): pass
    def update_agents(self): pass  
    def update_events(self): pass
    def update_focus(self, title="", content=""): pass
    def add_event(self, icon, agent, message, level="info"): pass
    def start_phase(self, phase_name): pass
    def update_phase_progress(self, phase_name, progress): pass
    def complete_phase(self, phase_name, success=True): pass
    def start_agent(self, agent_name, task=""): pass
    def update_agent_progress(self, agent_name, progress, metrics=None): pass
    def complete_agent(self, agent_name, success=True): pass
    def refresh(self): pass
    def render(self): return None

    def _get_default_focus_content(self) -> str:
        """Get default content for focus panel."""
        active_agents = [
            a for a in self.agents.values() if a.status == AgentStatus.RUNNING
        ]

        if active_agents:
            agent = active_agents[0]
            return f"Active: {agent.display_name}\nTask: {agent.current_task}\nProgress: {agent.progress}%"
        else:
            running_phases = [p for p in self.phases if p.status == PhaseStatus.RUNNING]
            if running_phases:
                phase = running_phases[0]
                return f"Phase: {phase.display_name}\nProgress: {phase.progress}%\nDuration: {phase.duration:.1f}s"
            else:
                return "System ready\nAwaiting tasks..."

    def add_event(self, icon: str, agent: str, message: str, level: str = "info"):
        """Add new event to the timeline."""
        event = EventInfo(
            timestamp=time.time(), icon=icon, agent=agent, message=message, level=level
        )
        self.events.append(event)

        # Keep only last 50 events
        if len(self.events) > 50:
            self.events = self.events[-50:]

    def start_phase(self, phase_name: str):
        """Start a phase."""
        for phase in self.phases:
            if phase.name == phase_name:
                phase.status = PhaseStatus.RUNNING
                phase.start_time = time.time()
                self.add_event("🚀", "System", f"Starting {phase.display_name} phase")
                break

    def update_phase_progress(self, phase_name: str, progress: int):
        """Update phase progress."""
        for phase in self.phases:
            if phase.name == phase_name:
                phase.progress = progress
                if phase.start_time:
                    phase.duration = time.time() - phase.start_time
                break

    def complete_phase(self, phase_name: str, success: bool = True):
        """Complete a phase."""
        for phase in self.phases:
            if phase.name == phase_name:
                phase.status = PhaseStatus.COMPLETED if success else PhaseStatus.FAILED
                phase.progress = 100 if success else phase.progress
                if phase.start_time:
                    phase.duration = time.time() - phase.start_time

                icon = "✅" if success else "❌"
                self.add_event(icon, "System", f"{phase.display_name} phase completed")
                break

    def start_agent(self, agent_name: str, task: str = ""):
        """Start an agent."""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.status = AgentStatus.RUNNING
            agent.current_task = task
            agent.progress = 0
            self.add_event("⚡", agent.display_name, f"Starting: {task}")

    def update_agent_progress(
        self, agent_name: str, progress: int, metrics: Dict[str, Any] = None
    ):
        """Update agent progress and metrics."""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.progress = progress
            if metrics:
                agent.metrics.update(metrics)

    def complete_agent(self, agent_name: str, success: bool = True):
        """Complete an agent."""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.status = AgentStatus.COMPLETED if success else AgentStatus.FAILED
            agent.progress = 100 if success else agent.progress

            icon = "✅" if success else "❌"
            self.add_event(icon, agent.display_name, "Task completed")

    def refresh(self):
        """Disabled to prevent terminal spam."""
        pass

    def render(self):
        """Disabled to prevent terminal spam."""
        return None

    def create_final_summary(self) -> str:
        """Create final execution summary."""
        total_duration = time.time() - self.start_time

        summary_lines = [
            f"🎉 Completed in {int(total_duration//60):02d}:{int(total_duration%60):02d}",
            "",
        ]

        # Phase summaries
        for phase in self.phases:
            if phase.status in [PhaseStatus.COMPLETED, PhaseStatus.FAILED]:
                status_icon = "✅" if phase.status == PhaseStatus.COMPLETED else "❌"
                summary_lines.append(
                    f"- {phase.display_name}: {phase.duration:02.0f}s {status_icon}"
                )

        summary_lines.extend(
            ["", "Artifacts:", "  - execution_report.json", "  - agent_metrics.json"]
        )

        return "\n".join(summary_lines)


# Global UI instance
_terminal_ui = None


def get_terminal_ui() -> SmartTerminalUI:
    """Get global terminal UI instance."""
    global _terminal_ui
    if _terminal_ui is None:
        _terminal_ui = SmartTerminalUI()
    return _terminal_ui


def initialize_terminal_ui(
    project_name: str = "smart-cli", branch: str = "main"
) -> SmartTerminalUI:
    """Initialize terminal UI with project info."""
    global _terminal_ui
    _terminal_ui = SmartTerminalUI(project_name, branch)
    return _terminal_ui
