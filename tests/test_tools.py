import pytest
from pathlib import Path
from tools.shell_tool import ShellTool
from tools.git_tool import GitTool
from tools.github_tool import GitHubTool
from tools.docker_tool import DockerTool
from tools.test_tool import TestTool
from config import Config

def test_shell_tool_allowlist():
    res = ShellTool.run_command("python --version")
    assert res["status"] == "success"
    assert "Python" in res["stdout"] or "Python" in res["stderr"]

    # Blocked dangerous command
    blocked = ShellTool.run_command("powershell_malicious_cmd")
    assert blocked["status"] == "blocked"

def test_git_tool_workspace_and_diff(tmp_path):
    git_tool = GitTool(workspace_base=tmp_path)
    ws = git_tool.create_isolated_workspace("test_wf", str(Config.DEMO_REPO_DIR))
    assert ws.exists()
    assert (ws / "config.py").exists()

    # Modify file
    mod_res = git_tool.apply_file_modification(ws, "config.py", "# New test content\nDATABASE_URL = 'sqlite://'")
    assert mod_res["had_original"] is True

    # Compute diff
    diff = git_tool.generate_diff(Config.DEMO_REPO_DIR, ws)
    assert "--- a/config.py" in diff
    assert "+++ b/config.py" in diff

def test_github_tool():
    gh = GitHubTool()
    info = gh.get_repo_info("devflow-demo/flask-demo-api")
    assert "name" in info

    pr = gh.create_pull_request("flask-demo-api", "Fix 500 error", "Details", "fix/devflow-123")
    assert pr["status"] in ("created", "proposed")
    assert "html_url" in pr

def test_docker_tool_simulation():
    res = DockerTool._simulate_docker_validation("test-image:latest", 5000)
    assert res["status"] == "SUCCESS"
    assert res["health_status"] == "HEALTHY"
    assert len(res["checks_passed"]) > 0
