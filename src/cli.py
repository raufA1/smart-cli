"""Main CLI entry point for Smart CLI."""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from utils.config import ConfigManager
from commands.generate import generate_app
from commands.init import init_app
from commands.review import review_app

# Initialize console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="smart-cli",
    help="AI-powered CLI tool for code generation and project management",
    add_completion=False,
    rich_markup_mode="rich",
)

# Add sub-applications
app.add_typer(generate_app, name="generate", help="Generate code using AI")
app.add_typer(init_app, name="init", help="Initialize new projects")
app.add_typer(review_app, name="review", help="Review and analyze code")


@app.command()
def version():
    """Show Smart CLI version information."""
    from . import __version__, __author__
    
    table = Table(title="Smart CLI Version Info")
    table.add_column("Field", style="bold blue")
    table.add_column("Value", style="green")
    
    table.add_row("Version", __version__)
    table.add_row("Author", __author__)
    table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    console.print(table)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key"),
    value: Optional[str] = typer.Option(None, "--value", help="Configuration value"),
):
    """Manage Smart CLI configuration."""
    config_manager = ConfigManager()
    
    if show:
        config_data = config_manager.get_all_config()
        table = Table(title="Smart CLI Configuration")
        table.add_column("Key", style="bold blue")
        table.add_column("Value", style="green")
        
        for key, val in config_data.items():
            # Hide sensitive data
            if "key" in key.lower() or "token" in key.lower() or "password" in key.lower():
                val = "***hidden***"
            table.add_row(key, str(val))
        
        console.print(table)
    
    elif set_key and value:
        config_manager.set_config(set_key, value)
        console.print(f"✅ Set {set_key} = {value}", style="green")
    
    else:
        console.print("Use --show to display config or --set with --value to update", style="yellow")


@app.command()
def health():
    """Check Smart CLI health and dependencies."""
    from utils.health_checker import HealthChecker
    import asyncio
    
    async def run_checks():
        health_checker = HealthChecker()
        results = await health_checker.run_health_checks()
        
        status_color = "green" if results["status"] == "healthy" else "red"
        console.print(f"Overall Status: {results['status'].upper()}", style=f"bold {status_color}")
        
        table = Table(title="Health Check Results")
        table.add_column("Component", style="bold")
        table.add_column("Status", style="bold")
        table.add_column("Details")
        
        for name, check in results["checks"].items():
            status_style = "green" if check["status"] == "healthy" else "red"
            details = check.get("details", check.get("error", ""))
            table.add_row(name, check["status"], str(details))
        
        console.print(table)
    
    asyncio.run(run_checks())


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()