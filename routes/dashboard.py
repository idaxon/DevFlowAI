from flask import Blueprint, render_template, jsonify, request
from database.models import Repository, Workflow, SystemLog, Deployment
from services.workflow_service import WorkflowService
from config import Config

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    return render_template("dashboard.html", demo_mode=Config.DEMO_MODE)

@dashboard_bp.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    repos = Repository.query.all()
    workflows = Workflow.query.order_by(Workflow.started_at.desc()).limit(10).all()
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(25).all()
    recent_deps = Deployment.query.order_by(Deployment.created_at.desc()).limit(5).all()
    analytics = WorkflowService.get_analytics_summary()

    active_wf_count = Workflow.query.filter(Workflow.status.in_(["RUNNING", "QUEUED", "AWAITING_APPROVAL"])).count()
    success_count = Workflow.query.filter(Workflow.status.in_(["SUCCESS", "APPROVED"])).count()
    failed_count = Workflow.query.filter_by(status="FAILED").count()

    return jsonify({
        "status": "operational",
        "demo_mode": Config.DEMO_MODE,
        "metrics": {
            "repositories": len(repos),
            "active_workflows": active_wf_count,
            "success_rate": f"{analytics['completion_rate']}%",
            "avg_execution": f"{analytics['avg_execution_time']}s",
            "successful_tasks": success_count,
            "failed_tasks": failed_count,
        },
        "recent_workflows": [w.to_dict() for w in workflows],
        "recent_logs": [log.to_dict() for log in recent_logs],
        "deployments": [d.to_dict() for d in recent_deps],
        "repositories_list": [r.to_dict() for r in repos],
    })
