from flask import Blueprint, render_template, jsonify, request
from database.models import AgentRun
from services.diagnosis_service import DiagnosisService
from config import Config

agents_bp = Blueprint("agents", __name__)

@agents_bp.route("/agents")
def agents_view():
    return render_template("agents.html", demo_mode=Config.DEMO_MODE)

@agents_bp.route("/troubleshoot")
def troubleshooting_view():
    return render_template("troubleshooting.html", demo_mode=Config.DEMO_MODE)

@agents_bp.route("/api/agents", methods=["GET"])
def get_agents_api():
    agent_types = [
        {"name": "IntentAgent", "role": "Intent & Goal Parser", "status": "ONLINE", "model": Config.OPENAI_MODEL if not Config.DEMO_MODE else "Demo Engine"},
        {"name": "TroubleshootingAgent", "role": "Root Cause & Evidence Analyzer", "status": "ONLINE", "model": "RAG-Enhanced Diagnostics"},
        {"name": "DebuggingAgent", "role": "Code Synthesis & Minimal Patching", "status": "ONLINE", "model": "Safe Sandbox Mutator"},
        {"name": "TestingAgent", "role": "Automated Pytest Runner", "status": "ONLINE", "model": "Pytest Engine"},
        {"name": "DeploymentAgent", "role": "Docker Build & Health Validator", "status": "ONLINE", "model": "Docker Sandbox"},
        {"name": "MonitoringAgent", "role": "Post-Deployment Telemetry", "status": "ONLINE", "model": "Health Prober"},
    ]
    return jsonify(agent_types)

@agents_bp.route("/api/troubleshoot", methods=["POST"])
def troubleshoot_api():
    data = request.get_json() or {}
    query = data.get("query")
    logs = data.get("logs", "")
    repo_id = data.get("repo_id", "demo")

    if not query:
        return jsonify({"error": "Troubleshooting query is required"}), 400

    res = DiagnosisService.diagnose_issue(query=query, repo_id=repo_id, logs=logs)
    return jsonify(res)
