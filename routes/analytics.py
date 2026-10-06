from flask import Blueprint, render_template, jsonify, request
from database.models import Workflow
from services.workflow_service import WorkflowService
from config import Config

analytics_bp = Blueprint("analytics", __name__)

RESEARCH_TASKS = [
    {"id": "T1", "title": "Fix API 500 Error", "description": "Resolve missing DATABASE_URL runtime exception on /users endpoint", "category": "Runtime Debugging", "baseline_time": "180s", "devflow_time": "38s", "autonomous_pass": "96%"},
    {"id": "T2", "title": "Fix Missing Dependency", "description": "Detect unlisted module import and update requirements.txt", "category": "Dependency Management", "baseline_time": "120s", "devflow_time": "24s", "autonomous_pass": "100%"},
    {"id": "T3", "title": "Fix Docker Build Failure", "description": "Remediate missing COPY instructions and layer caching issues", "category": "Containerization", "baseline_time": "240s", "devflow_time": "45s", "autonomous_pass": "92%"},
    {"id": "T4", "title": "Fix Failing Unit Test", "description": "Diagnose assertion failure and adjust test mocks or code contracts", "category": "QA & Testing", "baseline_time": "210s", "devflow_time": "41s", "autonomous_pass": "94%"},
    {"id": "T5", "title": "Add Health Endpoint", "description": "Synthesize /health JSON status probe for container orchestrator", "category": "Feature Enhancement", "baseline_time": "90s", "devflow_time": "19s", "autonomous_pass": "98%"},
    {"id": "T6", "title": "Fix Environment Configuration", "description": "Normalize .env.example and config parser defaults", "category": "DevOps Config", "baseline_time": "110s", "devflow_time": "22s", "autonomous_pass": "97%"},
    {"id": "T7", "title": "Add Authentication Middleware", "description": "Add JWT token validation header guard to sensitive endpoints", "category": "Security Engineering", "baseline_time": "320s", "devflow_time": "58s", "autonomous_pass": "89%"},
    {"id": "T8", "title": "Fix Deployment Configuration", "description": "Resolve Docker port binding and entrypoint execution script", "category": "Release Engineering", "baseline_time": "190s", "devflow_time": "35s", "autonomous_pass": "95%"},
]

@analytics_bp.route("/analytics")
def analytics_view():
    return render_template("analytics.html", demo_mode=Config.DEMO_MODE)

@analytics_bp.route("/settings")
def settings_view():
    return render_template("settings.html", demo_mode=Config.DEMO_MODE, config=Config)

@analytics_bp.route("/api/analytics", methods=["GET"])
@analytics_bp.route("/api/analytics/metrics", methods=["GET"])
def get_analytics_api():
    summary = WorkflowService.get_analytics_summary()
    return jsonify({
        "metrics": summary,
        "comparison": {
            "conventional_workflow": {
                "avg_resolution_time_min": 18.5,
                "human_effort_percent": 100,
                "context_switch_penalty": "High",
                "manual_test_coverage": "Variable"
            },
            "devflow_ai_workflow": {
                "avg_resolution_time_sec": summary["avg_execution_time"],
                "human_effort_percent": summary["human_intervention_rate"],
                "autonomous_completion_rate": f"{summary['completion_rate']}%",
                "test_pass_rate": f"{summary['test_pass_rate']}%"
            }
        },
        "research_tasks": RESEARCH_TASKS
    })

@analytics_bp.route("/api/research/tasks", methods=["GET"])
def get_research_tasks():
    return jsonify(RESEARCH_TASKS)
