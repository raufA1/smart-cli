"""Main CLI entry point for Smart CLI - Interactive AI Assistant."""

import asyncio
import os
import sys

import typer
from rich.console import Console

# Add src directory to Python path for imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Import new modular Smart CLI
try:
    from .smart_cli import SmartCLI
except ImportError:
    from smart_cli import SmartCLI

# Initialize console for rich output
console = Console()

# Create main Typer app for interactive mode only
app = typer.Typer(
    name="smart",
    help="🚀 Smart CLI - Interactive AI Assistant",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version information"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """🚀 Smart CLI - Interactive AI Assistant

    Start an interactive chat session with AI to help with development tasks.
    """
    if version:
        show_version()
        return

    # Always start interactive chat session when no subcommand
    if ctx.invoked_subcommand is None:
        smart_cli = SmartCLI(debug=debug)
        asyncio.run(smart_cli.start())


def show_version():
    """Show Smart CLI version information."""
    from rich.table import Table

    table = Table(title="Smart CLI Version Info")
    table.add_column("Field", style="bold blue")
    table.add_column("Value", style="green")

    table.add_row("Version", "1.0.0")
    table.add_row("Description", "Interactive AI Assistant")
    table.add_row(
        "Python Version",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

    console.print(table)


if __name__ == "__main__":
    app()
