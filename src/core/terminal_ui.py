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
    """Advanced terminal UI for Smart CLI with full dashboard."""

    def __init__(self, project_name: str = "unknown", branch: str = "main"):
        self.project_name = project_name
        self.branch = branch
        self.run_id = f"#{datetime.now().strftime('%Y-%m-%d-%H')}"
        self.start_time = time.time()

        # UI state
        self.phases: List[PhaseInfo] = [
            PhaseInfo("analysis", "Analysis"),
            PhaseInfo("architecture", "Architecture"),
            PhaseInfo("implementation", "Implementation"),
            PhaseInfo("testing", "Testing"),
            PhaseInfo("review", "Review"),
            PhaseInfo("meta", "Meta"),
        ]

        self.agents: Dict[str, AgentInfo] = {
            "analyzer": AgentInfo("analyzer", "Analyzer", "🔍"),
            "architect": AgentInfo("architect", "Architect", "🏗️"),
            "modifier": AgentInfo("modifier", "Modifier", "🔧"),
            "tester": AgentInfo("tester", "Tester", "🧪"),
            "reviewer": AgentInfo("reviewer", "Reviewer", "👁️"),
            "debug": AgentInfo("debug", "Debug", "🪲"),
        }

        self.events: List[EventInfo] = []
        self.current_focus = "overview"
        self.focus_content = ""

        # Layout setup
        self.layout = Layout()
        self.setup_layout()

    def setup_layout(self):
        """Setup the terminal layout structure."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=8),
            Layout(name="main"),
            Layout(name="footer", size=1),
        )

        # Split main area
        self.layout["main"].split_row(
            Layout(name="agents", ratio=1), Layout(name="right")
        )

        # Split right area
        self.layout["right"].split_column(
            Layout(name="events", ratio=1), Layout(name="focus", ratio=1)
        )

    def update_header(
        self,
        model: str = "Claude Sonnet",
        cache: bool = True,
        concurrency: int = 3,
        tty: bool = True,
    ):
        """Update header panel with project info."""
        header_text = Text.assemble(
            ("📦 Project: ", "bold blue"),
            (f"{self.project_name} ", "white"),
            ("│ Branch: ", "bold blue"),
            (f"{self.branch} ", "white"),
            ("│ RunID: ", "bold blue"),
            (f"{self.run_id}", "white"),
        )

        info_text = Text.assemble(
            ("Model: ", "bold blue"),
            (f"{model} ", "white"),
            ("│ Cache: ", "bold blue"),
            ("ON " if cache else "OFF ", "green" if cache else "red"),
            ("│ Concurrency: ", "bold blue"),
            (f"{concurrency} ", "white"),
            ("│ TTY: ", "bold blue"),
            ("True" if tty else "False", "green" if tty else "red"),
        )

        header_panel = Panel(
            Align.center(Text.assemble(header_text, "\n", info_text)),
            title="Smart CLI",
            border_style="blue",
        )

        self.layout["header"].update(header_panel)

    def update_progress(self):
        """Update phase progress bars."""
        progress_table = Table.grid(padding=1)
        progress_table.add_column(width=3)
        progress_table.add_column(width=15)
        progress_table.add_column(width=20)
        progress_table.add_column(width=8)
        progress_table.add_column(width=10)

        for i, phase in enumerate(self.phases, 1):
            # Progress bar
            filled = int(phase.progress / 100 * 10)
            bar = "■" * filled + "□" * (10 - filled)

            # Status icon
            if phase.status == PhaseStatus.RUNNING:
                icon = "⚡"
                color = "yellow"
            elif phase.status == PhaseStatus.COMPLETED:
                icon = "✅"
                color = "green"
            elif phase.status == PhaseStatus.FAILED:
                icon = "❌"
                color = "red"
            else:
                icon = "⏳"
                color = "dim"

            # Duration
            duration_text = f"{phase.duration:02.0f}s" if phase.duration > 0 else ""

            progress_table.add_row(
                f"{i})",
                phase.display_name,
                f"[{color}]{bar}[/{color}] {phase.progress}%",
                f"{icon}",
                duration_text,
            )

        progress_panel = Panel(
            progress_table, title="Phase Progress", border_style="blue"
        )
        self.layout["progress"].update(progress_panel)

    def update_agents(self):
        """Update agent status cards."""
        agents_table = Table.grid(padding=(0, 1))
        agents_table.add_column(width=2)  # emoji
        agents_table.add_column(width=12)  # name
        agents_table.add_column(width=35)  # metrics
        agents_table.add_column(width=3)  # status

        for agent_name, agent in self.agents.items():
            # Format metrics
            metrics_parts = []
            for key, value in agent.metrics.items():
                metrics_parts.append(f"{key}: {value}")
            metrics_text = (
                " | ".join(metrics_parts)
                if metrics_parts
                else agent.current_task or "idle"
            )

            # Status icon
            if agent.status == AgentStatus.RUNNING:
                status_icon = "⚡"
                status_color = "yellow"
            elif agent.status == AgentStatus.COMPLETED:
                status_icon = "✅"
                status_color = "green"
            elif agent.status == AgentStatus.FAILED:
                status_icon = "❌"
                status_color = "red"
            elif agent.status == AgentStatus.WAITING:
                status_icon = "⏳"
                status_color = "blue"
            else:
                status_icon = "💤"
                status_color = "dim"

            agents_table.add_row(
                agent.emoji,
                f"[cyan]{agent.display_name}[/cyan]",
                f"[dim]{metrics_text}[/dim]",
                f"[{status_color}]{status_icon}[/{status_color}]",
            )

        agents_panel = Panel(agents_table, title="Agents (live)", border_style="cyan")
        self.layout["agents"].update(agents_panel)

    def update_events(self):
        """Update events/notices panel."""
        events_table = Table.grid()
        events_table.add_column(width=6)  # timestamp
        events_table.add_column(width=3)  # icon
        events_table.add_column()  # message

        # Show last 8 events
        recent_events = self.events[-8:] if len(self.events) > 8 else self.events

        for event in recent_events:
            # Format timestamp (MM:SS)
            elapsed = event.timestamp - self.start_time
            timestamp_str = f"{int(elapsed//60):02d}:{int(elapsed%60):02d}"

            # Color based on level
            if event.level == "error":
                msg_color = "red"
            elif event.level == "warning":
                msg_color = "yellow"
            else:
                msg_color = "white"

            events_table.add_row(
                f"[dim]{timestamp_str}[/dim]",
                event.icon,
                f"[{msg_color}]{event.agent}: {event.message}[/{msg_color}]",
            )

        events_panel = Panel(
            events_table, title="Events / Notices", border_style="yellow"
        )
        self.layout["events"].update(events_panel)

    def update_focus(self, title: str = "System Status", content: str = ""):
        """Update focused panel with specific content."""
        if not content:
            content = self._get_default_focus_content()

        # Wrap content if too long
        if len(content) > 500:
            content = content[:500] + "..."

        focus_panel = Panel(content, title=title, border_style="green")
        self.layout["focus"].update(focus_panel)

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
        """Refresh all UI components."""
        self.update_header()
        self.update_progress()
        self.update_agents()
        self.update_events()
        self.update_focus()

    def render(self):
        """Render the complete UI layout."""
        self.refresh()
        return self.layout

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
