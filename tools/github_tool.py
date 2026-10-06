import logging
from typing import Dict, Any, List, Optional
from config import Config

logger = logging.getLogger("devflow.github")

class GitHubTool:
    """GitHub integration client with token authentication and Demo Mode simulation."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or Config.GITHUB_TOKEN
        self.client = None
        if self.token:
            try:
                from github import Github
                self.client = Github(self.token)
            except Exception as e:
                logger.warning(f"Failed to initialize PyGithub client: {e}")

    def is_connected(self) -> bool:
        return self.client is not None

    def get_repo_info(self, repo_full_name: str) -> Dict[str, Any]:
        if self.client:
            try:
                repo = self.client.get_repo(repo_full_name)
                return {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "default_branch": repo.default_branch,
                    "open_issues": repo.open_issues_count,
                    "stars": repo.stargazers_count,
                    "url": repo.html_url,
                }
            except Exception as e:
                logger.warning(f"Error fetching GitHub repo {repo_full_name}: {e}")

        # Fallback simulation
        return {
            "name": repo_full_name.split("/")[-1] if "/" in repo_full_name else repo_full_name,
            "full_name": repo_full_name,
            "default_branch": "main",
            "open_issues": 1,
            "stars": 12,
            "url": f"https://github.com/{repo_full_name}",
        }

    def create_pull_request(self, repo_name: str, title: str, body: str, head_branch: str, base_branch: str = "main") -> Dict[str, Any]:
        """Propose a pull request."""
        if self.client:
            try:
                repo = self.client.get_repo(repo_name)
                pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
                return {
                    "status": "created",
                    "pr_number": pr.number,
                    "html_url": pr.html_url,
                    "state": pr.state,
                }
            except Exception as e:
                logger.warning(f"Error creating live PR: {e}")

        # Simulated PR
        return {
            "status": "proposed",
            "pr_number": 42,
            "html_url": f"https://github.com/devflow-demo/{repo_name}/pull/42",
            "branch": head_branch,
            "state": "open",
        }
