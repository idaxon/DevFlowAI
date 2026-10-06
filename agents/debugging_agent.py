import time
import json
import logging
from typing import Dict, Any, List
from ai.llm_client import LLMClient
from ai.prompts import DEBUGGING_SYSTEM_PROMPT
from ai.schemas import DebuggingOutput

logger = logging.getLogger("devflow.agents.debugging")

class DebuggingAgent:
    """Agent that generates code modifications, patches, and unified diffs based on diagnosis."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def run(self, diagnosis: Dict[str, Any], rag_context: str, affected_files_content: Dict[str, str]) -> Dict[str, Any]:
        start_time = time.time()
        files_snippet = "\n".join([
            f"--- FILE: {fname} ---\n{content}\n" for fname, content in affected_files_content.items()
        ])

        user_prompt = (
            f"### ROOT CAUSE DIAGNOSIS:\n{json.dumps(diagnosis, indent=2)}\n\n"
            f"{rag_context}\n\n"
            f"### AFFECTED FILES CONTENT:\n{files_snippet}\n"
        )

        try:
            result = self.llm_client.generate_json(
                system_prompt=DEBUGGING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema_class=DebuggingOutput
            )
            duration = time.time() - start_time
            return {
                "status": "SUCCESS",
                "output": result,
                "duration": duration,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Debugging agent error: {e}")
            return {
                "status": "FAILED",
                "output": None,
                "duration": time.time() - start_time,
                "error": str(e),
            }
