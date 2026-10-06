import time
import logging
from pathlib import Path
from typing import Dict, Any
from tools.test_tool import TestTool

logger = logging.getLogger("devflow.agents.testing")

class TestingAgent:
    """Agent that executes pytest suites in isolated workspaces and parses results."""
    __test__ = False

    def __init__(self):
        self.test_tool = TestTool()

    def run(self, workspace_path: Path) -> Dict[str, Any]:
        start_time = time.time()
        try:
            result = self.test_tool.run_pytest(workspace_path)
            duration = time.time() - start_time
            return {
                "status": "SUCCESS" if result["status"] == "SUCCESS" else "FAILED",
                "output": result,
                "duration": duration,
                "error": None if result["status"] == "SUCCESS" else "One or more tests failed.",
            }
        except Exception as e:
            logger.error(f"Testing agent error: {e}")
            return {
                "status": "FAILED",
                "output": {
                    "status": "FAILED",
                    "total": 0,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "duration": time.time() - start_time,
                    "output_details": str(e),
                },
                "duration": time.time() - start_time,
                "error": str(e),
            }
