import time
import json
import logging
from typing import Dict, Any
from ai.llm_client import LLMClient
from ai.prompts import INTENT_SYSTEM_PROMPT
from ai.schemas import IntentOutput

logger = logging.getLogger("devflow.agents.intent")

class IntentAgent:
    """Agent that analyzes natural language developer requests to structure goals and execution plans."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def run(self, user_request: str) -> Dict[str, Any]:
        start_time = time.time()
        prompt = f"Analyze developer request:\n\n{user_request}"
        
        try:
            result = self.llm_client.generate_json(
                system_prompt=INTENT_SYSTEM_PROMPT,
                user_prompt=prompt,
                schema_class=IntentOutput
            )
            duration = time.time() - start_time
            return {
                "status": "SUCCESS",
                "output": result,
                "duration": duration,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Intent agent error: {e}")
            return {
                "status": "FAILED",
                "output": None,
                "duration": time.time() - start_time,
                "error": str(e),
            }
