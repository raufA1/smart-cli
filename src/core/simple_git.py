"""Smart CLI Simple Git Manager - Essential Git operations only."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class SimpleGitManager:
    """Minimal Git integration with essential operations."""

    def __init__(self):
        # Removed deprecated UI manager dependency
        self.repo_path = self._find_repo_root()

    def _find_repo_root(self) -> Optional[str]:
        """Find Git repository root."""
        current_path = Path.cwd()

        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return str(current_path)
            current_path = current_path.parent

        return None

    async def _run_git_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """Run Git command asynchronously."""
        if not self.repo_path:
            return False, "", "Not in a Git repository"

        cmd = ["git"] + args

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            success = process.returncode == 0

            return success, stdout.decode(), stderr.decode()

        except Exception as e:
            return False, "", str(e)

    async def check_git_status(self) -> Optional[dict]:
        """Get basic Git status."""
        if not self.repo_path:
            return None

        try:
            # Get branch name
            success, branch_output, _ = await self._run_git_command(
                ["branch", "--show-current"]
            )
            branch = branch_output.strip() if success else "unknown"

            # Get status
            success, status_output, _ = await self._run_git_command(
                ["status", "--porcelain"]
            )
            if not success:
                return None

            modified = []
            staged = []
            untracked = []

            for line in status_output.strip().split("\n"):
                if not line:
                    continue

                status_code = line[:2]
                filename = line[3:]

                if status_code[0] != " " and status_code[0] != "?":
                    staged.append(filename)
                if status_code[1] != " ":
                    modified.append(filename)
                if status_code == "??":
                    untracked.append(filename)

            return {
                "branch": branch,
                "modified": modified,
                "staged": staged,
                "untracked": untracked,
            }

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Git status failed", str(e))
            return None

    async def commit_changes(self, message: str) -> bool:
        """Commit all changes with message."""
        if not self.repo_path:
            if self.ui_manager:
                self.ui_manager.display_error("Not in a Git repository")
            return False

        try:
            # Stage all changes
            success, _, error = await self._run_git_command(["add", "-A"])
            if not success:
                if self.ui_manager:
                    self.ui_manager.display_error("Failed to stage changes", error)
                return False

            # Commit
            success, output, error = await self._run_git_command(
                ["commit", "-m", message]
            )

            if success:
                if self.ui_manager:
                    self.ui_manager.display_success("✅ Changes committed", output)
                return True
            else:
                if self.ui_manager:
                    self.ui_manager.display_error("Commit failed", error)
                return False

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Commit error", str(e))
            return False

    async def push_changes(self) -> bool:
        """Push changes to remote."""
        if not self.repo_path:
            return False

        try:
            success, output, error = await self._run_git_command(["push"])

            if success:
                if self.ui_manager:
                    self.ui_manager.display_success("✅ Changes pushed", output)
                return True
            else:
                if self.ui_manager:
                    self.ui_manager.display_error("Push failed", error)
                return False

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Push error", str(e))
            return False

    async def pull_changes(self) -> bool:
        """Pull changes from remote."""
        if not self.repo_path:
            return False

        try:
            success, output, error = await self._run_git_command(["pull"])

            if success:
                if self.ui_manager:
                    self.ui_manager.display_success("✅ Changes pulled", output)
                return True
            else:
                if self.ui_manager:
                    self.ui_manager.display_error("Pull failed", error)
                return False

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Pull error", str(e))
            return False

    async def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """Create new Git branch."""
        if not self.repo_path:
            return False

        try:
            # Create branch
            success, _, error = await self._run_git_command(["branch", branch_name])
            if not success:
                if self.ui_manager:
                    self.ui_manager.display_error(f"Failed to create branch", error)
                return False

            # Checkout if requested
            if checkout:
                success, _, error = await self._run_git_command(
                    ["checkout", branch_name]
                )
                if not success:
                    if self.ui_manager:
                        self.ui_manager.display_error(f"Failed to checkout", error)
                    return False

            if self.ui_manager:
                action = "created and checked out" if checkout else "created"
                self.ui_manager.display_success(f"Branch {branch_name} {action}")

            return True

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Branch creation failed", str(e))
            return False

    async def initialize_repo(self) -> bool:
        """Initialize new Git repository."""
        try:
            success, output, error = await self._run_git_command(["init"])

            if success:
                self.repo_path = os.getcwd()
                if self.ui_manager:
                    self.ui_manager.display_success("Git repository initialized")
                return True
            else:
                if self.ui_manager:
                    self.ui_manager.display_error(
                        "Repository initialization failed", error
                    )
                return False

        except Exception as e:
            if self.ui_manager:
                self.ui_manager.display_error("Init error", str(e))
            return False

    async def smart_commit(self, ai_client=None) -> bool:
        """Smart commit with AI-generated message."""
        status = await self.check_git_status()
        if not status:
            return False

        # Check if there are changes to commit
        total_changes = (
            len(status.get("modified", []))
            + len(status.get("staged", []))
            + len(status.get("untracked", []))
        )
        if total_changes == 0:
            if self.ui_manager:
                self.ui_manager.display_error("No changes to commit")
            return False

        # Generate commit message
        if ai_client:
            try:
                files_info = f"Modified: {status.get('modified', [])}, Staged: {status.get('staged', [])}, Untracked: {status.get('untracked', [])}"
                prompt = f"Generate a concise git commit message for these changes: {files_info}"

                response = await ai_client.generate_response(prompt)
                message = response.content.strip().split("\n")[0]  # First line only
            except:
                message = f"Smart CLI auto-commit: {total_changes} files changed"
        else:
            message = f"Smart CLI auto-commit: {total_changes} files changed"

        return await self.commit_changes(message)
