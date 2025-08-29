"""Git Operations Handler for Smart CLI."""

import time

from rich.console import Console

from .base_handler import BaseHandler

console = Console()


class GitHandler(BaseHandler):
    """Handler for Git operations and version control commands."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger Git operations."""
        return [
            "git",
            "commit",
            "push",
            "pull",
            "branch",
            "merge",
            "clone",
            "status",
            "log",
            "init",
            "add",
            "checkout",
            "repository",
            "repo",
            "version control",
            "commit et",
            "push et",
            "yeni branch",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle Git operations and version control commands."""
        if not self.matches_input(user_input):
            return False

        self.log_debug(f"Processing Git operation: {user_input}")
        await self._process_git_command(user_input)
        return True

    async def _process_git_command(self, command: str):
        """Process specific Git commands."""
        lower_cmd = command.lower()

        if "status" in lower_cmd:
            await self._handle_git_status()

        elif "init" in lower_cmd:
            await self._handle_git_init()

        elif "commit" in lower_cmd:
            await self._handle_git_commit()

        elif "push" in lower_cmd:
            await self._handle_git_push()

        elif "pull" in lower_cmd:
            await self._handle_git_pull()

        elif "branch" in lower_cmd and "new" in lower_cmd:
            await self._handle_new_branch(command)

        else:
            # Use AI to understand complex Git commands
            await self._handle_complex_git_command(command)

    async def _handle_git_status(self):
        """Handle git status command."""
        status = await self.smart_cli.git_manager.check_git_status()
        if status:
            status_info = f"Branch: {status['branch']}\\nModified: {len(status['modified'])}\\nStaged: {len(status['staged'])}\\nUntracked: {len(status['untracked'])}"
            self.ui_manager.display_ai_response(status_info, "Git Status")
        else:
            self.ui_manager.display_error("Not in a Git repository")

    async def _handle_git_init(self):
        """Handle git init command."""
        success = await self.smart_cli.git_manager.initialize_repo()
        if success:
            console.print("✅ [green]Git repository initialized[/green]")

    async def _handle_git_commit(self):
        """Handle git commit command."""
        await self.smart_cli.git_manager.smart_commit(self.ai_client)

    async def _handle_git_push(self):
        """Handle git push command."""
        await self.smart_cli.git_manager.push_changes()

    async def _handle_git_pull(self):
        """Handle git pull command."""
        await self.smart_cli.git_manager.pull_changes()

    async def _handle_new_branch(self, command: str):
        """Handle new branch creation."""
        words = command.split()
        branch_name = f"feature/smart-cli-{int(time.time())}"

        # Extract branch name if provided
        for i, word in enumerate(words):
            if word.lower() in ["branch", "yeni"] and i + 1 < len(words):
                branch_name = words[i + 1]
                break

        await self.smart_cli.git_manager.create_branch(branch_name)

    async def _handle_complex_git_command(self, command: str):
        """Handle complex Git commands using AI understanding."""
        if self.ai_client:
            enhanced_prompt = f"""
I need to perform this Git operation: "{command}"

Please provide the exact Git command(s) to execute this operation.
Focus on being practical and safe. If multiple steps are needed, list them clearly.
"""

            try:
                response = await self.ai_client.generate_response(enhanced_prompt)
                self.ui_manager.display_ai_response(response.content, "Git Assistant")
            except Exception as e:
                self.ui_manager.display_error("Git AI assistance failed", str(e))
        else:
            self.ui_manager.display_error(
                "Complex Git command not understood",
                "Try simpler commands like 'git status', 'git commit', 'git push'",
            )
