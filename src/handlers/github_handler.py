"""GitHub Operations Handler for Smart CLI."""

from rich.console import Console

from .base_handler import BaseHandler

console = Console()


class GitHubHandler(BaseHandler):
    """Handler for GitHub operations and repository management."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger GitHub operations."""
        return [
            "github",
            "repo",
            "repository",
            "pr",
            "pull request",
            "issue",
            "clone",
            "fork",
            "star",
            "commit",
            "push",
            "merge",
            "dashboard",
            "repos",
            "create repo",
            "list repos",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle GitHub operations and repository management."""
        if not self.smart_cli.github_manager:
            return False

        if not self.matches_input(user_input):
            return False

        self.log_debug(f"Processing GitHub operation: {user_input}")
        await self._process_github_command(user_input)
        return True

    async def _process_github_command(self, command: str):
        """Process GitHub commands with interactive interface."""
        lower_cmd = command.lower()

        try:
            if "dashboard" in lower_cmd:
                await self.smart_cli.github_manager.show_dashboard()

            elif any(
                word in lower_cmd for word in ["repos", "repositories", "list repos"]
            ):
                await self.smart_cli.github_manager.show_repository_list()

            elif any(word in lower_cmd for word in ["clone", "clone repo"]):
                await self.smart_cli.github_manager.clone_repository_interactive()

            elif any(
                word in lower_cmd for word in ["pr create", "create pr", "pull request"]
            ):
                await self.smart_cli.github_manager.create_pull_request_interactive()

            elif any(word in lower_cmd for word in ["help", "github help"]):
                await self.smart_cli.github_manager.show_github_help()

            else:
                # Show available GitHub commands
                self._show_github_help()

        except Exception as e:
            self.ui_manager.display_error("GitHub operation failed", str(e))

    def _show_github_help(self):
        """Show available GitHub commands."""
        console.print("🐙 [blue]Available GitHub Commands:[/blue]")
        console.print("   • [cyan]github dashboard[/cyan] - Show repository overview")
        console.print("   • [cyan]github repos[/cyan] - List your repositories")
        console.print("   • [cyan]github clone[/cyan] - Clone repository interactively")
        console.print("   • [cyan]github pr create[/cyan] - Create pull request")
        console.print("   • [cyan]github help[/cyan] - Show detailed GitHub help")
