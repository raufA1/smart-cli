"""Smart CLI GitHub Integration - Advanced repository management."""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


@dataclass
class GitHubRepo:
    """GitHub repository data structure."""

    name: str
    full_name: str
    description: str
    private: bool
    url: str
    clone_url: str
    default_branch: str
    language: str
    stars: int
    forks: int
    issues: int


@dataclass
class GitHubPR:
    """GitHub pull request data structure."""

    number: int
    title: str
    body: str
    state: str
    author: str
    branch: str
    target_branch: str
    url: str
    mergeable: bool
    created_at: str


@dataclass
class GitHubIssue:
    """GitHub issue data structure."""

    number: int
    title: str
    body: str
    state: str
    author: str
    labels: List[str]
    assignees: List[str]
    url: str
    created_at: str


class GitHubClient:
    """Advanced GitHub API client for Smart CLI."""

    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    async def initialize(self):
        """Initialize HTTP session."""
        if not self.session:
            headers = {
                "Authorization": f"token {self.token}" if self.token else "",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Smart-CLI/6.0.0",
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(
        self, method: str, endpoint: str, data: dict = None
    ) -> Dict[str, Any]:
        """Make authenticated GitHub API request."""
        await self.initialize()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(method, url, json=data) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get("X-RateLimit-Remaining", 0)
                )
                self.rate_limit_reset = int(
                    response.headers.get("X-RateLimit-Reset", 0)
                )

                if response.status == 200 or response.status == 201:
                    return await response.json()
                elif (
                    response.status == 403
                    and "rate limit" in (await response.text()).lower()
                ):
                    raise Exception("GitHub API rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise Exception(f"GitHub API error {response.status}: {error_text}")

        except Exception as e:
            raise Exception(f"GitHub request failed: {str(e)}")

    async def get_user_repos(
        self, username: str = None, org: str = None
    ) -> List[GitHubRepo]:
        """Get user or organization repositories."""
        if org:
            endpoint = f"orgs/{org}/repos"
        elif username:
            endpoint = f"users/{username}/repos"
        else:
            endpoint = "user/repos"

        repos_data = await self._make_request("GET", endpoint)

        repos = []
        for repo in repos_data:
            repos.append(
                GitHubRepo(
                    name=repo["name"],
                    full_name=repo["full_name"],
                    description=repo.get("description", ""),
                    private=repo["private"],
                    url=repo["html_url"],
                    clone_url=repo["clone_url"],
                    default_branch=repo["default_branch"],
                    language=repo.get("language", "Unknown"),
                    stars=repo["stargazers_count"],
                    forks=repo["forks_count"],
                    issues=repo["open_issues_count"],
                )
            )

        return repos

    async def get_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[GitHubPR]:
        """Get repository pull requests."""
        endpoint = f"repos/{owner}/{repo}/pulls"
        params = f"?state={state}"

        prs_data = await self._make_request("GET", f"{endpoint}{params}")

        prs = []
        for pr in prs_data:
            prs.append(
                GitHubPR(
                    number=pr["number"],
                    title=pr["title"],
                    body=pr.get("body", ""),
                    state=pr["state"],
                    author=pr["user"]["login"],
                    branch=pr["head"]["ref"],
                    target_branch=pr["base"]["ref"],
                    url=pr["html_url"],
                    mergeable=pr.get("mergeable", False),
                    created_at=pr["created_at"],
                )
            )

        return prs

    async def create_pull_request(
        self, owner: str, repo: str, title: str, body: str, head: str, base: str
    ) -> GitHubPR:
        """Create a new pull request."""
        endpoint = f"repos/{owner}/{repo}/pulls"
        data = {"title": title, "body": body, "head": head, "base": base}

        pr_data = await self._make_request("POST", endpoint, data)

        return GitHubPR(
            number=pr_data["number"],
            title=pr_data["title"],
            body=pr_data.get("body", ""),
            state=pr_data["state"],
            author=pr_data["user"]["login"],
            branch=pr_data["head"]["ref"],
            target_branch=pr_data["base"]["ref"],
            url=pr_data["html_url"],
            mergeable=pr_data.get("mergeable", False),
            created_at=pr_data["created_at"],
        )

    async def get_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[GitHubIssue]:
        """Get repository issues."""
        endpoint = f"repos/{owner}/{repo}/issues"
        params = f"?state={state}"

        issues_data = await self._make_request("GET", f"{endpoint}{params}")

        issues = []
        for issue in issues_data:
            # Skip pull requests (they appear as issues in GitHub API)
            if "pull_request" in issue:
                continue

            issues.append(
                GitHubIssue(
                    number=issue["number"],
                    title=issue["title"],
                    body=issue.get("body", ""),
                    state=issue["state"],
                    author=issue["user"]["login"],
                    labels=[label["name"] for label in issue.get("labels", [])],
                    assignees=[
                        assignee["login"] for assignee in issue.get("assignees", [])
                    ],
                    url=issue["html_url"],
                    created_at=issue["created_at"],
                )
            )

        return issues

    async def create_repository(
        self, name: str, description: str = "", private: bool = False
    ) -> GitHubRepo:
        """Create a new repository."""
        endpoint = "user/repos"
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
        }

        repo_data = await self._make_request("POST", endpoint, data)

        return GitHubRepo(
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description", ""),
            private=repo_data["private"],
            url=repo_data["html_url"],
            clone_url=repo_data["clone_url"],
            default_branch=repo_data["default_branch"],
            language=repo_data.get("language", "Unknown"),
            stars=repo_data["stargazers_count"],
            forks=repo_data["forks_count"],
            issues=repo_data["open_issues_count"],
        )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_time": (
                datetime.fromtimestamp(self.rate_limit_reset)
                if self.rate_limit_reset > 0
                else None
            ),
            "percentage": (self.rate_limit_remaining / 5000) * 100,
        }
