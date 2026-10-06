import os
import subprocess
import shlex
import logging
from typing import Dict, Any, List, Optional
from config import Config

logger = logging.getLogger("devflow.tools")

ALLOWED_COMMAND_PREFIXES = [
    "pytest",
    "python",
    "git",
    "docker",
    "pip",
    "npm",
    "node",
    "mvn",
    "cat",
    "ls",
    "dir",
    "echo",
]

class ShellTool:
    """Safeguarded command execution tool with timeouts and command allowlisting."""

    @staticmethod
    def run_command(command: str, cwd: Optional[str] = None, timeout: Optional[int] = None, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a shell command with strict timeouts and safety checks."""
        timeout_seconds = timeout or Config.MAX_EXECUTION_TIMEOUT
        
        # Security validation
        cmd_tokens = shlex.split(command, posix=False) if command else []
        if not cmd_tokens:
            return {"status": "error", "returncode": -1, "stdout": "", "stderr": "Empty command"}

        base_bin = cmd_tokens[0].lower().replace(".exe", "").replace(".cmd", "")
        # Strip path prefix if any
        base_bin = base_bin.split("\\")[-1].split("/")[-1]

        if base_bin not in ALLOWED_COMMAND_PREFIXES:
            return {
                "status": "blocked",
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command '{base_bin}' is not in DevFlow safe execution allowlist.",
            }

        # Setup environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=exec_env,
            )
            return {
                "status": "success" if process.returncode == 0 else "failed",
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds.",
            }
        except Exception as e:
            return {
                "status": "error",
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }
