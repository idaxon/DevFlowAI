from flask import Blueprint, render_template, jsonify, request
from database.db import db
from database.models import Workflow, Repository
from services.workflow_service import WorkflowService
from services.report_service import ReportService
from config import Config

workflows_bp = Blueprint("workflows", __name__)

@workflows_bp.route("/workflows")
def list_workflows_view():
    workflows = Workflow.query.order_by(Workflow.started_at.desc()).all()
    return render_template("workflow.html", workflows=workflows, demo_mode=Config.DEMO_MODE)

@workflows_bp.route("/workflows/<string:workflow_id>")
def workflow_detail_view(workflow_id):
    workflow = db.session.get(Workflow, workflow_id)
    return render_template("workflow.html", current_workflow=workflow, demo_mode=Config.DEMO_MODE)

@workflows_bp.route("/api/workflows", methods=["GET"])
def get_workflows_api():
    workflows = Workflow.query.order_by(Workflow.started_at.desc()).all()
    return jsonify([w.to_dict() for w in workflows])

@workflows_bp.route("/api/workflows/<string:workflow_id>", methods=["GET"])
def get_workflow_detail_api(workflow_id):
    wf = db.session.get(Workflow, workflow_id)
    if not wf:
        return jsonify({"error": "Workflow not found"}), 404
    return jsonify(wf.to_dict())

@workflows_bp.route("/api/workflows/run", methods=["POST"])
def run_workflow_api():
    data = request.get_json() or {}
    request_text = data.get("request")
    repo_id = data.get("repository_id")

    if not request_text:
        return jsonify({"error": "Request description is required"}), 400

    wf = WorkflowService.create_and_run_workflow(request_text=request_text, repo_id=repo_id)
    return jsonify({"status": "success", "workflow": wf.to_dict()}), 201

@workflows_bp.route("/api/workflows/<string:workflow_id>/approve", methods=["POST"])
def approve_workflow_api(workflow_id):
    res = WorkflowService.approve_workflow(workflow_id)
    return jsonify(res)

@workflows_bp.route("/api/workflows/<string:workflow_id>/reject", methods=["POST"])
def reject_workflow_api(workflow_id):
    data = request.get_json() or {}
    reason = data.get("reason", "Rejected by user")
    res = WorkflowService.reject_workflow(workflow_id, reason=reason)
    return jsonify(res)

@workflows_bp.route("/api/workflows/<string:workflow_id>/report", methods=["GET"])
def get_workflow_report_api(workflow_id):
    report = ReportService.generate_report(workflow_id)
    return jsonify(report)

@workflows_bp.route("/api/workflows/<string:workflow_id>/chat", methods=["POST"])
def workflow_chat_api(workflow_id):
    """Handle follow-up questions, code explanations, and next task requests."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    res = WorkflowService.chat_followup(workflow_id, message)
    return jsonify(res)

