"""Smart CLI Simple Terminal Manager - Essential command execution only."""

import asyncio
import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CommandResult:
    """Simple command result."""

    command: str
    success: bool
    output: str
    error: str


class SimpleTerminalManager:
    """Minimal terminal command execution."""

    def __init__(self):
        self.ui_manager = ui_manager
        self.current_directory = os.getcwd()

    async def execute_command(self, command: str) -> CommandResult:
        """Execute shell command safely."""

        # Basic safety check for dangerous commands
        dangerous = ["rm -rf", "sudo rm", "format", "mkfs", "dd if="]
        if any(danger in command.lower() for danger in dangerous):
            if self.ui_manager:
                self.ui_manager.display_error("⚠️ Dangerous command blocked", command)
            return CommandResult(command, False, "", "Dangerous command blocked")

        try:
            if self.ui_manager:
                self.ui_manager.console.print(f"🔧 [blue]Executing:[/blue] {command}")

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.current_directory,
            )

            stdout, stderr = await process.communicate()
            success = process.returncode == 0

            output = stdout.decode("utf-8", errors="ignore")
            error = stderr.decode("utf-8", errors="ignore")

            if self.ui_manager:
                if success and output:
                    self.ui_manager.console.print(
                        f"✅ [green]Output:[/green]\n{output}"
                    )
                elif not success and error:
                    self.ui_manager.console.print(f"❌ [red]Error:[/red]\n{error}")

            return CommandResult(command, success, output, error)

        except Exception as e:
            error_msg = str(e)
            if self.ui_manager:
                self.ui_manager.display_error("Command execution failed", error_msg)
            return CommandResult(command, False, "", error_msg)

    async def execute_with_ai_assistance(
        self, natural_command: str, ai_client=None
    ) -> CommandResult:
        """Convert natural language to shell command and execute."""

        if not ai_client:
            return CommandResult(natural_command, False, "", "No AI client available")

        prompt = f"""Convert this to a shell command (respond with command only):
"{natural_command}"

Examples:
- "list files" -> ls -la
- "check disk space" -> df -h
- "find python files" -> find . -name "*.py"

Command:"""

        try:
            if self.ui_manager:
                self.ui_manager.console.print(
                    "🤖 [blue]Converting to shell command...[/blue]"
                )

            response = await ai_client.generate_response(prompt)
            shell_command = response.content.strip().split("\n")[0]

            if self.ui_manager:
                self.ui_manager.console.print(
                    f"📝 [green]Converted to:[/green] {shell_command}"
                )

            return await self.execute_command(shell_command)

        except Exception as e:
            error_msg = str(e)
            if self.ui_manager:
                self.ui_manager.display_error("AI command conversion failed", error_msg)
            return CommandResult(natural_command, False, "", error_msg)

    def change_directory(self, path: str) -> bool:
        """Change current working directory."""
        try:
            expanded_path = os.path.expanduser(path)
            if os.path.isdir(expanded_path):
                self.current_directory = os.path.abspath(expanded_path)
                os.chdir(self.current_directory)

                if self.ui_manager:
                    self.ui_manager.console.print(
                        f"📁 [green]Changed to:[/green] {self.current_directory}"
                    )
                return True
            else:
                if self.ui_manager:
                    self.ui_manager.display_error(f"Directory not found: {path}")
                return False

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Directory change failed", str(e))
            return False

    async def smart_command_suggestion(self, task: str, ai_client=None) -> list:
        """Get AI command suggestions for a task."""

        if not ai_client:
            return []

        prompt = f"""Suggest 3 shell commands for: "{task}"

Format as numbered list:
1. command1
2. command2  
3. command3"""

        try:
            response = await ai_client.generate_response(prompt)
            suggestions = []

            for line in response.content.split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    cmd = line.split(".", 1)[-1].strip()
                    if cmd:
                        suggestions.append(cmd)

            return suggestions[:3]  # Max 3 suggestions

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Command suggestion failed", str(e))
            return []
