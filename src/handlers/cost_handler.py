"""Cost Management Handler for Smart CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .base_handler import BaseHandler

console = Console()


class CostHandler(BaseHandler):
    """Handler for AI cost management operations."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger cost operations."""
        return [
            "cost",
            "budget",
            "usage",
            "spending",
            "price",
            "money",
            "xərc",
            "büdcə",
            "pul",
            "məsrəf",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle cost management operations."""
        if not self._matches_cost_command(user_input):
            return False

        self.log_debug(f"Processing cost operation: {user_input}")
        await self._process_cost_command(user_input)
        return True

    def _matches_cost_command(self, user_input: str) -> bool:
        """Check if input matches cost management commands."""
        lower_input = user_input.lower()

        # Direct cost commands
        cost_phrases = [
            "cost status",
            "budget status",
            "usage report",
            "spending report",
            "cost limit",
            "set budget",
            "cost optimization",
            "cost report",
            "xərc hesabatı",
            "büdcə vəziyyəti",
            "məsrəf hesabatı",
        ]

        for phrase in cost_phrases:
            if phrase in lower_input:
                return True

        # Single keywords in cost context
        if any(keyword in lower_input for keyword in self.keywords):
            return True

        return False

    async def _process_cost_command(self, command: str):
        """Process cost management commands."""
        lower_cmd = command.lower()

        # Import cost optimizer
        try:
            from ..core.ai_cost_optimizer import get_cost_optimizer
        except ImportError:
            from core.ai_cost_optimizer import get_cost_optimizer
        cost_optimizer = get_cost_optimizer()

        # Profile commands first (before generic 'set' detection)
        if any(word in lower_cmd for word in ["profile", "preset", "template"]):
            await self._handle_profile_commands(command)

        elif any(
            word in lower_cmd
            for word in ["status", "report", "summary", "hesabat", "vəziyyət"]
        ):
            await self._show_cost_status(cost_optimizer)

        elif any(word in lower_cmd for word in ["limit", "set", "budget", "configure"]):
            if "set" in lower_cmd or "configure" in lower_cmd:
                await self._set_budget_limits(cost_optimizer, command)
            else:
                await self._configure_budget(cost_optimizer)

        elif any(word in lower_cmd for word in ["optimization", "optimize", "suggest"]):
            await self._show_optimization_suggestions(cost_optimizer)

        elif any(word in lower_cmd for word in ["models", "pricing", "price"]):
            await self._show_model_pricing(cost_optimizer)

        else:
            await self._show_cost_help()

    async def _show_cost_status(self, cost_optimizer):
        """Show current cost usage status."""
        status = cost_optimizer.get_budget_status()

        # Create usage table
        table = Table(title="💰 AI Cost Usage Status")
        table.add_column("Metric", style="bold blue")
        table.add_column("Current", style="cyan")
        table.add_column("Limit", style="green")
        table.add_column("Remaining", style="yellow")
        table.add_column(
            "Usage %", style="red" if status["daily_percentage"] > 80 else "green"
        )

        # Daily usage
        table.add_row(
            "Daily Budget",
            f"${status['daily_usage']:.3f}",
            f"${status['daily_limit']:.2f}",
            f"${status['daily_remaining']:.3f}",
            f"{status['daily_percentage']:.1f}%",
        )

        # Monthly usage
        monthly_percentage = (status["monthly_usage"] / status["monthly_limit"]) * 100
        table.add_row(
            "Monthly Budget",
            f"${status['monthly_usage']:.2f}",
            f"${status['monthly_limit']:.2f}",
            f"${status['monthly_remaining']:.2f}",
            f"{monthly_percentage:.1f}%",
        )

        console.print(table)

        # Status indicator
        if status["daily_percentage"] < 50:
            indicator = Panel("✅ Cost usage is healthy", border_style="green")
        elif status["daily_percentage"] < 80:
            indicator = Panel(
                "⚠️ Moderate usage - monitor carefully", border_style="yellow"
            )
        else:
            indicator = Panel(
                "🚨 High usage - consider optimization", border_style="red"
            )

        console.print(indicator)

    async def _show_model_pricing(self, cost_optimizer):
        """Show model pricing information."""
        table = Table(title="🤖 AI Model Pricing")
        table.add_column("Model", style="bold blue")
        table.add_column("Provider", style="cyan")
        table.add_column("Input/1K", style="green")
        table.add_column("Output/1K", style="yellow")
        table.add_column("Tier", style="magenta")
        table.add_column("Best For", style="white")

        for name, model in cost_optimizer.models.items():
            table.add_row(
                name.replace("-", " ").title(),
                model.provider,
                f"${model.cost_per_1k_input:.4f}",
                f"${model.cost_per_1k_output:.4f}",
                model.tier.value.title(),
                ", ".join(model.strengths[:2]),
            )

        console.print(table)

    async def _show_optimization_suggestions(self, cost_optimizer):
        """Show cost optimization suggestions."""
        # Mock agent usage data for suggestions
        agent_usage = {
            "analyzer": 0.5,
            "modifier": 1.2,
            "architect": 0.8,
            "tester": 0.3,
            "reviewer": 0.4,
        }

        suggestions = cost_optimizer.suggest_cost_optimization(agent_usage)

        console.print("💡 [bold blue]Cost Optimization Suggestions:[/bold blue]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"   {i}. {suggestion}")

        # Additional tips
        console.print("\n🎯 [bold]Pro Tips for Cost Reduction:[/bold]")
        console.print("   • Use simpler models for basic tasks")
        console.print("   • Enable aggressive caching for repeated operations")
        console.print("   • Batch similar requests together")
        console.print("   • Use local models for development/testing")
        console.print("   • Set stricter daily limits for automatic control")

    async def _configure_budget(self, cost_optimizer):
        """Show current budget configuration."""
        console.print("⚙️ [bold blue]Current Budget Configuration:[/bold blue]")
        console.print(f"   Daily limit: ${cost_optimizer.budget.daily_limit:.2f}")
        console.print(f"   Monthly limit: ${cost_optimizer.budget.monthly_limit:.2f}")
        console.print(
            f"   Per-request limit: ${cost_optimizer.budget.per_request_limit:.2f}"
        )
        console.print(
            f"   Emergency reserve: ${cost_optimizer.budget.emergency_reserve:.2f}"
        )

        console.print("\n💡 [cyan]To change limits:[/cyan]")
        console.print(
            "   • [yellow]cost set daily 10.00[/yellow] - Set daily limit to $10"
        )
        console.print(
            "   • [yellow]cost set monthly 200.00[/yellow] - Set monthly limit to $200"
        )
        console.print(
            "   • [yellow]cost set request 1.00[/yellow] - Set per-request limit to $1"
        )
        console.print(
            "   • [yellow]cost configure interactive[/yellow] - Interactive setup"
        )

    async def _set_budget_limits(self, cost_optimizer, command: str):
        """Set budget limits via command."""
        import re

        # Parse command for limit type and amount
        command_lower = command.lower()

        # Extract amount (look for numbers with optional decimal)
        amount_match = re.search(r"(\d+(?:\.\d{1,2})?)", command)
        if not amount_match:
            console.print(
                "❌ [red]Please specify an amount (e.g., 'cost set daily 10.00')[/red]"
            )
            return

        amount = float(amount_match.group(1))

        # Determine limit type
        if "daily" in command_lower or "günlük" in command_lower:
            await self._update_daily_limit(cost_optimizer, amount)
        elif "monthly" in command_lower or "aylıq" in command_lower:
            await self._update_monthly_limit(cost_optimizer, amount)
        elif "request" in command_lower or "per" in command_lower:
            await self._update_request_limit(cost_optimizer, amount)
        elif "interactive" in command_lower:
            await self._interactive_budget_setup(cost_optimizer)
        else:
            console.print(
                "❌ [red]Specify limit type: daily, monthly, or request[/red]"
            )
            console.print(
                "💡 Examples: 'cost set daily 15.00', 'cost set monthly 250.00'"
            )

    async def _update_daily_limit(self, cost_optimizer, amount: float):
        """Update daily budget limit."""
        if amount < 0.50:
            console.print(
                "⚠️ [yellow]Daily limit too low! Minimum recommended: $0.50[/yellow]"
            )
            return
        elif amount > 1000.00:
            console.print(
                "⚠️ [yellow]Daily limit very high! Are you sure? Consider monthly limits instead.[/yellow]"
            )

        old_limit = cost_optimizer.budget.daily_limit
        cost_optimizer.budget.daily_limit = amount

        # Update environment file
        await self._update_project_config("AI_DAILY_LIMIT", str(amount))

        console.print(
            f"✅ [green]Daily budget limit updated: ${old_limit:.2f} → ${amount:.2f}[/green]"
        )
        console.print("🔄 [blue]Restart Smart CLI to persist changes[/blue]")

    async def _update_monthly_limit(self, cost_optimizer, amount: float):
        """Update monthly budget limit."""
        if amount < cost_optimizer.budget.daily_limit * 5:
            console.print(
                "⚠️ [yellow]Monthly limit should be at least 5x daily limit[/yellow]"
            )

        old_limit = cost_optimizer.budget.monthly_limit
        cost_optimizer.budget.monthly_limit = amount

        await self._update_project_config("AI_MONTHLY_LIMIT", str(amount))

        console.print(
            f"✅ [green]Monthly budget limit updated: ${old_limit:.2f} → ${amount:.2f}[/green]"
        )
        console.print("🔄 [blue]Restart Smart CLI to persist changes[/blue]")

    async def _update_request_limit(self, cost_optimizer, amount: float):
        """Update per-request budget limit."""
        if amount > cost_optimizer.budget.daily_limit:
            console.print(
                "⚠️ [yellow]Per-request limit higher than daily limit![/yellow]"
            )

        old_limit = cost_optimizer.budget.per_request_limit
        cost_optimizer.budget.per_request_limit = amount

        await self._update_project_config("AI_REQUEST_LIMIT", str(amount))

        console.print(
            f"✅ [green]Per-request limit updated: ${old_limit:.2f} → ${amount:.2f}[/green]"
        )
        console.print("🔄 [blue]Restart Smart CLI to persist changes[/blue]")

    async def _update_project_config(self, key: str, value: str):
        """Update project configuration in .smart/ directory."""
        import os
        import json
        from pathlib import Path
        from datetime import datetime

        smart_dir = Path(".smart")
        config_file = smart_dir / "budget.json"
        
        # Create .smart directory if it doesn't exist
        if not smart_dir.exists():
            console.print("📝 [blue]Creating .smart/ directory for project settings...[/blue]")
            try:
                smart_dir.mkdir()
                console.print("✅ [green].smart/ directory created![/green]")
            except Exception as e:
                console.print(f"❌ [red]Failed to create .smart/ directory: {e}[/red]")
                return
        
        # Load existing config or create new
        config = {}
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
            except Exception:
                config = {}
        
        # Update configuration
        config[key] = value
        config["updated_at"] = str(datetime.now())
        
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            console.print(f"✅ [green]Budget setting updated in .smart/budget.json[/green]")
        except Exception as e:
            console.print(f"❌ [red]Failed to update project config: {e}[/red]")


    async def _interactive_budget_setup(self, cost_optimizer):
        """Interactive budget configuration wizard."""
        console.print("🧙‍♂️ [bold blue]Interactive Budget Setup Wizard[/bold blue]")
        console.print("Current limits:")
        console.print(f"   Daily: ${cost_optimizer.budget.daily_limit:.2f}")
        console.print(f"   Monthly: ${cost_optimizer.budget.monthly_limit:.2f}")
        console.print(f"   Per-request: ${cost_optimizer.budget.per_request_limit:.2f}")

        console.print("\n💡 [cyan]Usage recommendations:[/cyan]")
        console.print(
            "   🟢 Light usage (few requests/day): Daily $2-5, Monthly $50-100"
        )
        console.print(
            "   🟡 Medium usage (regular development): Daily $5-15, Monthly $100-300"
        )
        console.print(
            "   🔴 Heavy usage (production/team): Daily $15-50, Monthly $300-1000"
        )

        console.print("\n🔧 [yellow]To set new limits, use specific commands:[/yellow]")
        console.print("   • cost set daily 10.00")
        console.print("   • cost set monthly 200.00")
        console.print("   • cost set request 1.00")

    async def _handle_profile_commands(self, command: str):
        """Handle profile-related commands."""
        try:
            from ..core.budget_profiles import UsageProfile, get_profile_manager
        except ImportError:
            from core.budget_profiles import UsageProfile, get_profile_manager

        profile_manager = get_profile_manager()
        command_lower = command.lower()

        if "list" in command_lower or "show" in command_lower:
            await self._show_budget_profiles(profile_manager)
        elif "set" in command_lower or "apply" in command_lower:
            await self._apply_budget_profile(profile_manager, command)
        elif "compare" in command_lower:
            await self._compare_profiles(profile_manager)
        elif "recommend" in command_lower:
            await self._recommend_profile(profile_manager)
        else:
            await self._show_profile_help()

    async def _show_budget_profiles(self, profile_manager):
        """Show all available budget profiles."""
        table = Table(title="💳 Budget Profiles")
        table.add_column("Profile", style="bold blue")
        table.add_column("Description", style="cyan")
        table.add_column("Daily", style="green")
        table.add_column("Monthly", style="yellow")
        table.add_column("Per-Request", style="magenta")

        for profile_type, profile in profile_manager.list_profiles().items():
            table.add_row(
                profile.name,
                (
                    profile.description[:50] + "..."
                    if len(profile.description) > 50
                    else profile.description
                ),
                f"${profile.daily_limit:.2f}",
                f"${profile.monthly_limit:.2f}",
                f"${profile.per_request_limit:.2f}",
            )

        console.print(table)
        console.print(
            "\n💡 [cyan]To apply a profile: cost profile set developer[/cyan]"
        )

    async def _apply_budget_profile(self, profile_manager, command: str):
        """Apply a budget profile."""
        import re

        # Extract profile name from command
        words = command.lower().split()
        profile_name = None

        # Look for profile name after 'set' or 'apply'
        for i, word in enumerate(words):
            if word in ["set", "apply"] and i + 1 < len(words):
                profile_name = words[i + 1]
                break

        if not profile_name:
            console.print("❌ [red]Please specify a profile name[/red]")
            console.print(
                "💡 Available profiles: student, developer, freelancer, startup, enterprise, unlimited"
            )
            return

        try:
            # Get profile by name first (this handles the enum conversion internally)
            profile = profile_manager.get_profile_by_name(profile_name)

            # Find the matching UsageProfile enum
            profile_enum = None
            for p_type, p_profile in profile_manager.list_profiles().items():
                if p_profile.name.lower() == profile_name.lower():
                    profile_enum = p_type
                    break

            if not profile_enum:
                raise ValueError(f"Profile '{profile_name}' not found")

            # Apply profile to session manager if available
            if hasattr(self.smart_cli, 'session_manager'):
                self.smart_cli.session_manager.set_budget_profile(profile_enum)

            env_vars = profile_manager.apply_profile(profile_enum)

            # Update environment variables
            for key, value in env_vars.items():
                await self._update_project_config(key, value)

            console.print(f"✅ [green]Applied '{profile.name}' budget profile![/green]")
            console.print(f"   Daily limit: ${profile.daily_limit:.2f}")
            console.print(f"   Monthly limit: ${profile.monthly_limit:.2f}")
            console.print(f"   Per-request limit: ${profile.per_request_limit:.2f}")
            console.print("🔄 [blue]Restart Smart CLI to apply changes[/blue]")

        except ValueError as e:
            console.print(f"❌ [red]{e}[/red]")
            console.print("💡 Use 'cost profile list' to see available profiles")

    async def _compare_profiles(self, profile_manager):
        """Compare cost between different profiles."""
        comparison = profile_manager.get_cost_comparison()

        table = Table(title="💰 Profile Cost Comparison")
        table.add_column("Profile", style="bold blue")
        table.add_column("Daily", style="green")
        table.add_column("Monthly", style="yellow")
        table.add_column("Annual Est.", style="red")
        table.add_column("Cost/1K Req.", style="cyan")

        for profile_name, costs in comparison.items():
            table.add_row(
                profile_name,
                f"${costs['daily_limit']:.2f}",
                f"${costs['monthly_limit']:.2f}",
                f"${costs['annual_cost_estimate']:.0f}",
                f"${costs['cost_per_1k_requests_estimate']:.0f}",
            )

        console.print(table)

    async def _recommend_profile(self, profile_manager):
        """Recommend a profile based on usage patterns."""
        console.print("🧙‍♂️ [bold blue]Profile Recommendation Wizard[/bold blue]")
        console.print("\n❓ Based on your usage patterns:")
        console.print("   🟢 Light usage (1-5 requests/day) → Student Profile")
        console.print("   🟡 Regular usage (10-30 requests/day) → Developer Profile")
        console.print(
            "   🟠 Heavy usage (50+ requests/day) → Freelancer/Startup Profile"
        )
        console.print("   🔴 Enterprise usage (100+ requests/day) → Enterprise Profile")

        console.print(
            "\n💡 [cyan]To set a profile: cost profile set [profile_name][/cyan]"
        )

    async def _show_profile_help(self):
        """Show profile management help."""
        console.print("📋 [bold blue]Budget Profile Commands:[/bold blue]")
        console.print(
            "   • [cyan]cost profile list[/cyan] - Show all available profiles"
        )
        console.print(
            "   • [cyan]cost profile set developer[/cyan] - Apply developer profile"
        )
        console.print("   • [cyan]cost profile compare[/cyan] - Compare profile costs")
        console.print(
            "   • [cyan]cost profile recommend[/cyan] - Get profile recommendations"
        )
        console.print(
            "\n💡 Profiles automatically configure optimal budgets and models!"
        )

    async def _show_cost_help(self):
        """Show cost management help."""
        console.print("💰 [bold blue]Cost Management Commands:[/bold blue]")
        console.print(
            "   • [cyan]cost status[/cyan] - Show current usage and budget status"
        )
        console.print("   • [cyan]cost report[/cyan] - Detailed usage report")
        console.print("   • [cyan]cost models[/cyan] - Show model pricing information")
        console.print("   • [cyan]cost optimize[/cyan] - Get optimization suggestions")
        console.print("   • [cyan]cost budget[/cyan] - Show budget configuration")
        console.print("\n🔧 [bold blue]Budget Configuration:[/bold blue]")
        console.print("   • [cyan]cost set daily 15.00[/cyan] - Set daily limit to $15")
        console.print(
            "   • [cyan]cost set monthly 300.00[/cyan] - Set monthly limit to $300"
        )
        console.print(
            "   • [cyan]cost set request 2.00[/cyan] - Set per-request limit to $2"
        )
        console.print(
            "   • [cyan]cost configure interactive[/cyan] - Interactive budget setup"
        )
        console.print("\n📋 [bold blue]Budget Profiles:[/bold blue]")
        console.print("   • [cyan]cost profile list[/cyan] - Show available profiles")
        console.print(
            "   • [cyan]cost profile set developer[/cyan] - Apply developer profile"
        )
        console.print("   • [cyan]cost profile compare[/cyan] - Compare profile costs")
        console.print(
            "\n💡 Smart CLI automatically selects cost-effective models for each task!"
        )
