import time
import logging
from pathlib import Path
from typing import Dict, Any
from tools.docker_tool import DockerTool

logger = logging.getLogger("devflow.agents.deployment")

class DeploymentAgent:
    """Agent that builds Docker image, runs container in sandbox, and validates health."""

    def __init__(self):
        self.docker_tool = DockerTool()

    def run(self, workspace_path: Path, tag: str = "devflow-app:test") -> Dict[str, Any]:
        start_time = time.time()
        try:
            result = self.docker_tool.build_and_validate(workspace_path, tag=tag)
            duration = time.time() - start_time
            return {
                "status": "SUCCESS" if result.get("status") == "SUCCESS" else "FAILED",
                "output": result,
                "duration": duration,
                "error": None if result.get("status") == "SUCCESS" else result.get("message"),
            }
        except Exception as e:
            logger.error(f"Deployment agent error: {e}")
            return {
                "status": "FAILED",
                "output": {
                    "status": "FAILED",
                    "image": tag,
                    "health_status": "UNHEALTHY",
                    "logs": str(e),
                },
                "duration": time.time() - start_time,
                "error": str(e),
            }
