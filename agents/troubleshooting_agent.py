import time
import json
import logging
from typing import Dict, Any, List, Optional
from ai.llm_client import LLMClient
from ai.prompts import TROUBLESHOOTING_SYSTEM_PROMPT
from ai.schemas import TroubleshootingOutput

logger = logging.getLogger("devflow.agents.troubleshoot")

class TroubleshootingAgent:
    """Agent that performs root cause analysis based on RAG code context and error logs."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def run(
        self,
        user_request: str,
        rag_context: str,
        error_logs: str = "",
        repo_file_context: str = ""
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Include real repo file context in the prompt for repo-specific, unique diagnosis
        repo_section = ""
        if repo_file_context:
            repo_section = f"\n### ACTUAL REPOSITORY CODE SCAN:\n{repo_file_context}\n"

        user_prompt = (
            f"### DEVELOPER REQUEST:\n{user_request}\n\n"
            f"{rag_context}\n"
            f"{repo_section}\n"
            f"### RUNTIME / TEST ERROR LOGS:\n{error_logs if error_logs else 'No explicit runtime logs provided.'}\n"
        )

        try:
            result = self.llm_client.generate_json(
                system_prompt=TROUBLESHOOTING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema_class=TroubleshootingOutput
            )
            duration = time.time() - start_time
            return {
                "status": "SUCCESS",
                "output": result,
                "duration": duration,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Troubleshooting agent error: {e}")
            return {
                "status": "FAILED",
                "output": None,
                "duration": time.time() - start_time,
                "error": str(e),
            }
