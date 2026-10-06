import pytest
from ai.llm_client import LLMClient
from agents.intent_agent import IntentAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from agents.debugging_agent import DebuggingAgent
from agents.testing_agent import TestingAgent
from agents.deployment_agent import DeploymentAgent
from config import Config

def test_intent_agent():
    llm = LLMClient()
    agent = IntentAgent(llm)
    res = agent.run("Fix the HTTP 500 error on /users endpoint and run tests.")
    assert res["status"] == "SUCCESS"
    assert res["output"]["intent"] in ("troubleshooting", "debugging", "general")
    assert res["output"].get("requires_testing", res["output"].get("testing_required", True)) in (True, False)

def test_troubleshooting_agent():
    llm = LLMClient()
    agent = TroubleshootingAgent(llm)
    res = agent.run(
        user_request="My Flask API is returning HTTP 500 on /users",
        rag_context="config.py: DATABASE_URL = os.environ.get('DATABASE_URL')\ndatabase.py: init_db sets db_instance to None if DATABASE_URL is empty.",
        error_logs="RuntimeError: Database connection failure: DATABASE_URL is not configured"
    )
    assert res["status"] == "SUCCESS"
    diag = res["output"]
    assert "DATABASE_URL" in diag["root_cause"] or "database" in diag["root_cause"].lower() or "config" in diag["root_cause"].lower()
    assert diag["confidence"] > 0.5
    assert len(diag["affected_files"]) > 0

def test_debugging_agent():
    llm = LLMClient()
    agent = DebuggingAgent(llm)
    res = agent.run(
        diagnosis={"root_cause": "Missing DATABASE_URL fallback in config.py"},
        rag_context="config.py: DATABASE_URL = os.environ.get('DATABASE_URL')",
        affected_files_content={"config.py": "class Config:\n    DATABASE_URL = os.environ.get('DATABASE_URL')"}
    )
    assert res["status"] == "SUCCESS"
    debug_out = res["output"]
    assert "diff" in debug_out or "combined_diff" in debug_out or "patches" in debug_out

def test_deployment_agent():
    agent = DeploymentAgent()
    res = agent.run(Config.DEMO_REPO_DIR)
    assert res["status"] == "SUCCESS"
    assert res["output"]["health_status"] == "HEALTHY"
