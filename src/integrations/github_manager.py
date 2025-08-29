"""Smart CLI GitHub Manager - High-level GitHub operations with beautiful UI."""

import asyncio
import os
import subprocess
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from .github_client import GitHubClient, GitHubIssue, GitHubPR, GitHubRepo

console = Console()


class GitHubManager:
    """High-level GitHub operations manager for Smart CLI."""

    def __init__(self, ui_manager=None):
        self.github = GitHubClient()
        self.ui_manager = ui_manager
        self.current_repo = self._detect_current_repo()

    def _detect_current_repo(self) -> Optional[Dict[str, str]]:
        """Detect current Git repository."""
        try:
            # Get remote origin URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL
                if "github.com" in url:
                    # Handle both SSH and HTTPS URLs
                    if url.startswith("git@github.com:"):
                        repo_path = url.replace("git@github.com:", "").replace(
                            ".git", ""
                        )
                    elif url.startswith("https://github.com/"):
                        repo_path = url.replace("https://github.com/", "").replace(
                            ".git", ""
                        )
                    else:
                        return None

                    owner, repo = repo_path.split("/")
                    return {"owner": owner, "repo": repo}

            return None
        except Exception:
            return None

    async def show_dashboard(self):
        """Display GitHub dashboard with repository overview."""
        if not self.current_repo:
            console.print("❌ [red]Not in a GitHub repository[/red]")
            return

        console.print("📊 [bold blue]GitHub Repository Dashboard[/bold blue]\n")

        try:
            # Get repository info
            owner, repo = self.current_repo["owner"], self.current_repo["repo"]

            with console.status("🔍 Loading GitHub data..."):
                # Fetch data concurrently
                repo_task = self.github.get_user_repos()
                prs_task = self.github.get_pull_requests(owner, repo)
                issues_task = self.github.get_issues(owner, repo)

                repos = await repo_task
                prs = await prs_task
                issues = await issues_task

            # Find current repo in list
            current_repo_data = None
            for r in repos:
                if r.name == repo:
                    current_repo_data = r
                    break

            if current_repo_data:
                # Repository overview panel
                repo_info = f"""
🏷️  **Repository:** {current_repo_data.full_name}
📝  **Description:** {current_repo_data.description or 'No description'}
🔒  **Visibility:** {'Private' if current_repo_data.private else 'Public'}
⭐  **Stars:** {current_repo_data.stars}
🍴  **Forks:** {current_repo_data.forks}
🐛  **Open Issues:** {current_repo_data.issues}
💻  **Language:** {current_repo_data.language}
🌿  **Default Branch:** {current_repo_data.default_branch}
                """.strip()

                repo_panel = Panel(
                    repo_info, title="📊 Repository Overview", border_style="blue"
                )
                console.print(repo_panel)

            # Create layout with columns
            layout = Layout()
            layout.split_row(Layout(name="left"), Layout(name="right"))

            # Pull Requests Table
            pr_table = Table(
                title="🔄 Open Pull Requests",
                show_header=True,
                header_style="bold magenta",
            )
            pr_table.add_column("#", style="dim", width=6)
            pr_table.add_column("Title", style="cyan")
            pr_table.add_column("Author", style="green", width=12)
            pr_table.add_column("Branch", style="yellow", width=15)

            for pr in prs[:5]:  # Show first 5 PRs
                pr_table.add_row(
                    f"#{pr.number}",
                    pr.title[:40] + "..." if len(pr.title) > 40 else pr.title,
                    pr.author,
                    pr.branch,
                )

            # Issues Table
            issues_table = Table(
                title="🐛 Open Issues", show_header=True, header_style="bold red"
            )
            issues_table.add_column("#", style="dim", width=6)
            issues_table.add_column("Title", style="cyan")
            issues_table.add_column("Author", style="green", width=12)
            issues_table.add_column("Labels", style="yellow", width=15)

            for issue in issues[:5]:  # Show first 5 issues
                labels_str = ", ".join(issue.labels[:2]) if issue.labels else "None"
                issues_table.add_row(
                    f"#{issue.number}",
                    issue.title[:40] + "..." if len(issue.title) > 40 else issue.title,
                    issue.author,
                    labels_str,
                )

            # Display tables side by side
            layout["left"].update(Panel(pr_table, border_style="green"))
            layout["right"].update(Panel(issues_table, border_style="red"))
            console.print(layout)

            # Rate limit status
            rate_limit = self.github.get_rate_limit_status()
            rate_limit_text = f"API Calls Remaining: {rate_limit['remaining']}/5000 ({rate_limit['percentage']:.1f}%)"
            console.print(f"\n💡 [dim]{rate_limit_text}[/dim]")

        except Exception as e:
            console.print(f"❌ [red]GitHub API error: {str(e)}[/red]")
        finally:
            await self.github.close()

    async def create_pull_request_interactive(self):
        """Interactive pull request creation with AI assistance."""
        if not self.current_repo:
            console.print("❌ [red]Not in a GitHub repository[/red]")
            return

        console.print("🔄 [bold green]Create Pull Request[/bold green]\n")

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else "main"

            # Interactive input
            title = Prompt.ask("📝 Pull Request Title")
            body = Prompt.ask("📄 Description (optional)", default="")
            target_branch = Prompt.ask("🎯 Target Branch", default="main")

            if not title:
                console.print("❌ [red]Title is required[/red]")
                return

            # Confirm creation
            console.print(f"\n📋 [bold]PR Preview:[/bold]")
            console.print(f"   Title: {title}")
            console.print(f"   Branch: {current_branch} → {target_branch}")
            console.print(f"   Description: {body or 'No description'}")

            if Confirm.ask("🚀 Create this pull request?"):
                with console.status("🔄 Creating pull request..."):
                    owner, repo = self.current_repo["owner"], self.current_repo["repo"]
                    pr = await self.github.create_pull_request(
                        owner, repo, title, body, current_branch, target_branch
                    )

                console.print(f"✅ [green]Pull request created successfully![/green]")
                console.print(f"🔗 URL: {pr.url}")
                console.print(f"📋 PR #{pr.number}: {pr.title}")

        except Exception as e:
            console.print(f"❌ [red]Failed to create PR: {str(e)}[/red]")
        finally:
            await self.github.close()

    async def show_repository_list(self, username: str = None, org: str = None):
        """Show beautiful repository list."""
        console.print("📚 [bold blue]GitHub Repositories[/bold blue]\n")

        try:
            with console.status("🔍 Loading repositories..."):
                repos = await self.github.get_user_repos(username, org)

            if not repos:
                console.print("📂 [yellow]No repositories found[/yellow]")
                return

            # Create repository table
            repo_table = Table(show_header=True, header_style="bold cyan")
            repo_table.add_column("Repository", style="cyan", width=25)
            repo_table.add_column("Description", style="white", width=40)
            repo_table.add_column("Language", style="green", width=12)
            repo_table.add_column("⭐", justify="right", width=8)
            repo_table.add_column("🍴", justify="right", width=8)
            repo_table.add_column("🐛", justify="right", width=8)

            for repo in repos[:20]:  # Show first 20 repos
                visibility_icon = "🔒" if repo.private else "📂"
                repo_name = f"{visibility_icon} {repo.name}"

                description = (
                    repo.description[:37] + "..."
                    if len(repo.description) > 40
                    else repo.description
                )
                description = description or "No description"

                repo_table.add_row(
                    repo_name,
                    description,
                    repo.language or "Unknown",
                    str(repo.stars),
                    str(repo.forks),
                    str(repo.issues),
                )

            repo_panel = Panel(
                repo_table,
                title=f"📊 Repository List ({len(repos)} total)",
                border_style="blue",
            )
            console.print(repo_panel)

        except Exception as e:
            console.print(f"❌ [red]Failed to load repositories: {str(e)}[/red]")
        finally:
            await self.github.close()

    async def clone_repository_interactive(self):
        """Interactive repository cloning with directory selection."""
        console.print("📦 [bold green]Clone GitHub Repository[/bold green]\n")

        # Get repository URL
        repo_url = Prompt.ask("🔗 Repository URL or owner/repo")

        if not repo_url:
            console.print("❌ [red]Repository URL is required[/red]")
            return

        # Parse repository info
        if "/" in repo_url and "github.com" not in repo_url:
            # Format: owner/repo
            owner, repo_name = repo_url.split("/")
            clone_url = f"https://github.com/{owner}/{repo_name}.git"
        elif "github.com" in repo_url:
            # Full GitHub URL
            clone_url = repo_url
            repo_name = repo_url.split("/")[-1].replace(".git", "")
        else:
            console.print("❌ [red]Invalid repository format[/red]")
            return

        # Get target directory
        current_dir = os.getcwd()
        target_dir = Prompt.ask(
            "📁 Clone to directory", default=f"{current_dir}/{repo_name}"
        )

        # Confirm cloning
        console.print(f"\n📋 [bold]Clone Details:[/bold]")
        console.print(f"   Repository: {clone_url}")
        console.print(f"   Target: {target_dir}")

        if Confirm.ask("📦 Clone this repository?"):
            try:
                with console.status(f"📦 Cloning {repo_name}..."):
                    result = subprocess.run(
                        ["git", "clone", clone_url, target_dir],
                        capture_output=True,
                        text=True,
                    )

                if result.returncode == 0:
                    console.print(f"✅ [green]Repository cloned successfully![/green]")
                    console.print(f"📁 Location: {target_dir}")

                else:
                    console.print(f"❌ [red]Clone failed: {result.stderr}[/red]")

            except Exception as e:
                console.print(f"❌ [red]Clone error: {str(e)}[/red]")

    async def show_github_help(self):
        """Show GitHub integration help and commands."""
        help_text = """
🐙 **GitHub Integration Commands:**

📊 **Repository Management:**
   • `smart github dashboard` - Repository overview
   • `smart github repos` - List repositories  
   • `smart github clone` - Interactive clone
   • `smart github create` - Create new repository

🔄 **Pull Requests:**
   • `smart github pr create` - Create pull request
   • `smart github pr list` - List open PRs
   • `smart github pr merge` - Merge pull request

🐛 **Issues:**
   • `smart github issues` - List open issues
   • `smart github issue create` - Create new issue

⚙️ **Setup:**
   • Set GITHUB_TOKEN environment variable
   • Or add to Smart CLI config: `smart config set github_token YOUR_TOKEN`

💡 **Tips:**
   • Use `smart github status` to check API rate limits
   • All GitHub operations integrate with Smart CLI todo system
   • PRs and issues are automatically tracked in your todos
        """.strip()

        help_panel = Panel(
            help_text, title="🐙 GitHub Integration Help", border_style="green"
        )
        console.print(help_panel)
