"""Terminal Operations Handler for Smart CLI."""

from rich.console import Console
from rich.table import Table

from .base_handler import BaseHandler

console = Console()


class TerminalHandler(BaseHandler):
    """Handler for terminal command execution requests."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger terminal operations."""
        return [
            "run",
            "execute",
            "command",
            "shell",
            "terminal",
            "bash",
            "işlet",
            "çalıştır",
            "komut",
            "cmd",
            "$",
            "ls",
            "cd",
            "pwd",
            "python",
            "node",
            "npm",
            "pip",
            "curl",
            "wget",
            "grep",
            "find",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle terminal command execution requests."""
        lower_input = user_input.lower()

        # Skip AI-like questions (contain these patterns)
        ai_question_patterns = [
            "what is",
            "what are",
            "explain",
            "difference between",
            "how to",
            "why",
            "when",
            "where",
            "necə",
            "niyə",
            "nə vaxt",
        ]

        if any(pattern in lower_input for pattern in ai_question_patterns):
            return False

        # Check if it looks like a direct shell command (starts with common commands)
        starts_with_command = any(
            lower_input.startswith(cmd + " ") or lower_input == cmd
            for cmd in [
                "ls",
                "pwd",
                "cd",
                "cat",
                "grep",
                "find",
                "python3",
                "node",
                "npm",
                "pip",
            ]
        )

        # Only handle if it's clearly a terminal command
        if starts_with_command:
            self.log_debug(f"Processing terminal command: {user_input}")
            await self._process_terminal_command(user_input)
            return True

        # Check for explicit run/execute keywords with commands
        if any(word in lower_input for word in ["run", "execute", "işlet", "çalıştır"]):
            # Only if it contains actual command words
            has_command = any(
                cmd in lower_input
                for cmd in ["ls", "pwd", "python", "node", "npm", "git"]
            )
            if has_command:
                self.log_debug(f"Processing requested command: {user_input}")
                await self._process_terminal_command(user_input)
                return True

        return False

    async def _process_terminal_command(self, command: str):
        """Process terminal commands with AI assistance."""
        lower_cmd = command.lower()

        # Handle directory changes specially
        if lower_cmd.startswith("cd "):
            path = command[3:].strip()
            self.smart_cli.terminal_manager.change_directory(path)
            return

        # Handle direct commands (already look like shell commands)
        direct_commands = [
            "ls",
            "pwd",
            "cat",
            "grep",
            "find",
            "python",
            "node",
            "npm",
            "pip",
        ]
        if any(command.strip().startswith(cmd) for cmd in direct_commands):
            await self.smart_cli.terminal_manager.execute_command(command.strip())
            return

        # Handle natural language requests
        if any(word in lower_cmd for word in ["run", "execute", "işlet", "çalıştır"]):
            # Extract the actual command
            actual_command = self._extract_command_from_natural_language(
                command, lower_cmd
            )
            if actual_command:
                await self.smart_cli.terminal_manager.execute_command(actual_command)
                return

        # Use AI to convert natural language to command
        if "command" in lower_cmd or "komut" in lower_cmd:
            await self.smart_cli.terminal_manager.execute_with_ai_assistance(
                command, self.ai_client
            )
            return

        # Handle command suggestions
        if any(
            word in lower_cmd for word in ["how to", "necə", "suggest", "təklif et"]
        ):
            suggestions = (
                await self.smart_cli.terminal_manager.smart_command_suggestion(
                    command, self.ai_client
                )
            )
            if suggestions:
                self._display_command_suggestions(suggestions, command)
            return

        # Default: try to execute as-is if it looks like a command
        if len(command.split()) <= 5 and not any(
            char in command for char in ["?", "what", "how", "nə", "necə"]
        ):
            await self.smart_cli.terminal_manager.execute_command(command.strip())
        else:
            # Use AI assistance for complex requests
            await self.smart_cli.terminal_manager.execute_with_ai_assistance(
                command, self.ai_client
            )

    def _extract_command_from_natural_language(
        self, command: str, lower_cmd: str
    ) -> str:
        """Extract actual command from natural language request."""
        for prefix in ["run ", "execute ", "işlet ", "çalıştır "]:
            if prefix in lower_cmd:
                actual_command = command[
                    command.lower().find(prefix) + len(prefix) :
                ].strip()
                if actual_command:
                    return actual_command
        return ""

    def _display_command_suggestions(self, suggestions: list, original_request: str):
        """Display command suggestions in beautiful format."""
        suggestion_table = Table(show_header=True, header_style="bold green")
        suggestion_table.add_column("#", style="yellow", width=3)
        suggestion_table.add_column("Suggested Command", style="cyan")
        suggestion_table.add_column("Description", style="white")

        for i, cmd in enumerate(suggestions, 1):
            # Simple description based on command
            description = self._get_command_description(cmd)
            suggestion_table.add_row(str(i), cmd, description)

        console.print(
            f"\\n[bold green]💡 Command Suggestions for: {original_request}[/bold green]"
        )
        console.print(suggestion_table)
        console.print(
            "\\n[dim]💡 Type the command number or full command to execute[/dim]"
        )

    def _get_command_description(self, cmd: str) -> str:
        """Get simple description for command."""
        descriptions = {
            "ls": "List files and directories",
            "pwd": "Show current directory",
            "cd": "Change directory",
            "cat": "Display file contents",
            "grep": "Search text in files",
            "find": "Search for files",
            "python": "Run Python script",
            "pip": "Install Python packages",
            "npm": "Node.js package manager",
            "curl": "Download from URL",
            "wget": "Download files",
            "df": "Show disk usage",
            "ps": "Show running processes",
        }

        first_word = cmd.split()[0] if cmd.split() else cmd
        return descriptions.get(first_word, "Execute command")
