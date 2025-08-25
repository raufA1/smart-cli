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
from utils.usage_tracker import UsageTracker
from commands.generate import generate_app as basic_generate_app
from commands.ai_generate import generate_app as ai_generate_app
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
app.add_typer(ai_generate_app, name="generate", help="Generate code using AI")
app.add_typer(basic_generate_app, name="template", help="Generate basic templates")
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


@app.command()
def usage(
    period: str = typer.Option("daily", "--period", "-p", help="Period: daily, weekly, monthly"),
    export: bool = typer.Option(False, "--export", help="Export usage data"),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv"),
):
    """Show usage statistics and cost tracking."""
    usage_tracker = UsageTracker()
    
    if export:
        from datetime import datetime, timedelta
        
        # Export last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        try:
            data = usage_tracker.export_usage_data(start_date, end_date, format)
            filename = f"smart_cli_usage_{end_date.strftime('%Y%m%d')}.{format}"
            
            with open(filename, 'w') as f:
                f.write(data)
            
            console.print(f"✅ Usage data exported to {filename}", style="green")
            
        except Exception as e:
            console.print(f"❌ Export failed: {str(e)}", style="red")
        
        return
    
    # Show usage statistics
    if period == "daily":
        usage_data = usage_tracker.get_daily_usage()
    elif period == "weekly":
        usage_data = usage_tracker.get_weekly_usage()
    elif period == "monthly":
        usage_data = usage_tracker.get_monthly_usage()
    else:
        console.print("❌ Invalid period. Use: daily, weekly, monthly", style="red")
        return
    
    # Display usage summary
    overall = usage_data['overall']
    
    summary_table = Table(title=f"{period.title()} Usage Summary")
    summary_table.add_column("Metric", style="blue")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Requests", str(overall['total_requests']))
    summary_table.add_row("Total Tokens", f"{overall['total_tokens']:,}")
    summary_table.add_row("Estimated Cost", f"${overall['total_estimated_cost']:.4f}")
    
    if overall['total_actual_cost']:
        summary_table.add_row("Actual Cost", f"${overall['total_actual_cost']:.4f}")
    
    summary_table.add_row("Avg Cost/Request", f"${overall['average_cost_per_request']:.4f}")
    
    console.print(summary_table)
    
    # Show budget status
    budget_status = usage_tracker.check_budget_status()
    
    budget_table = Table(title="Budget Status")
    budget_table.add_column("Period", style="blue")
    budget_table.add_column("Budget", style="cyan")
    budget_table.add_column("Spent", style="yellow")
    budget_table.add_column("Remaining", style="green")
    budget_table.add_column("Usage %", style="red")
    
    for period_name, status in budget_status.items():
        usage_pct = f"{status['percentage_used']:.1f}%"
        if status['over_budget']:
            usage_pct += " ⚠️"
        
        budget_table.add_row(
            period_name.title(),
            f"${status['budget']:.2f}",
            f"${status['spent']:.4f}",
            f"${status['remaining']:.4f}",
            usage_pct
        )
    
    console.print(budget_table)
    
    # Show top usage patterns
    top_patterns = usage_tracker.get_top_usage_patterns(5)
    
    if top_patterns:
        patterns_table = Table(title="Top Usage Patterns (Last 30 Days)")
        patterns_table.add_column("Type", style="blue")
        patterns_table.add_column("Model", style="cyan")
        patterns_table.add_column("Count", style="green")
        patterns_table.add_column("Total Cost", style="yellow")
        patterns_table.add_column("Avg Cost", style="red")
        
        for pattern in top_patterns:
            patterns_table.add_row(
                pattern['usage_type'],
                pattern['model'],
                str(pattern['usage_count']),
                f"${pattern['total_cost']:.4f}",
                f"${pattern['average_cost']:.4f}"
            )
        
        console.print(patterns_table)


@app.command()
def budget(
    set_budget: Optional[str] = typer.Option(None, "--set", help="Set budget: daily, weekly, monthly"),
    amount: Optional[float] = typer.Option(None, "--amount", help="Budget amount"),
):
    """Manage usage budgets."""
    usage_tracker = UsageTracker()
    
    if set_budget and amount:
        if usage_tracker.set_budget(set_budget, amount):
            console.print(f"✅ {set_budget.title()} budget set to ${amount:.2f}", style="green")
        else:
            console.print("❌ Invalid budget type. Use: daily, weekly, monthly", style="red")
    else:
        # Show current budget status
        budget_status = usage_tracker.check_budget_status()
        
        table = Table(title="Current Budget Configuration")
        table.add_column("Period", style="blue")
        table.add_column("Budget", style="cyan")
        table.add_column("Spent", style="yellow")
        table.add_column("Remaining", style="green")
        table.add_column("Status", style="red")
        
        for period, status in budget_status.items():
            status_text = "Over Budget ⚠️" if status['over_budget'] else "OK ✅"
            
            table.add_row(
                period.title(),
                f"${status['budget']:.2f}",
                f"${status['spent']:.4f}",
                f"${status['remaining']:.4f}",
                status_text
            )
        
        console.print(table)
        console.print("\n💡 Set budgets with: smart-cli budget --set daily --amount 5.00", style="dim")


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