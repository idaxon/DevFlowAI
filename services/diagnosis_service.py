import logging
from typing import Dict, Any, Optional
from ai.llm_client import LLMClient
from agents.troubleshooting_agent import TroubleshootingAgent
from rag.retriever import RepositoryRetriever
from tools.log_tool import LogTool

logger = logging.getLogger("devflow.services.diagnosis")

class DiagnosisService:
    """Service to execute standalone troubleshooting queries or log diagnostics."""

    @staticmethod
    def diagnose_issue(query: str, repo_id: Optional[str] = "demo", logs: str = "") -> Dict[str, Any]:
        """Perform dedicated root cause diagnosis."""
        llm = LLMClient()
        agent = TroubleshootingAgent(llm)
        retriever = RepositoryRetriever(repo_id=str(repo_id or "demo"))
        
        chunks = retriever.retrieve(query + " " + logs[:200], top_k=4)
        rag_context = retriever.format_context_for_prompt(chunks)

        res = agent.run(user_request=query, rag_context=rag_context, error_logs=logs)
        return {
            "status": res["status"],
            "diagnosis": res["output"],
            "retrieved_files": [c["path"] for c in chunks],
            "duration": res["duration"],
        }
