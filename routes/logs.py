from flask import Blueprint, render_template, jsonify, request
from database.models import SystemLog
from config import Config

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs")
def logs_view():
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(100).all()
    return render_template("logs.html", logs=logs, demo_mode=Config.DEMO_MODE)

@logs_bp.route("/api/logs", methods=["GET"])
def get_logs_api():
    workflow_id = request.args.get("workflow_id")
    query = SystemLog.query
    if workflow_id:
        query = query.filter_by(workflow_id=workflow_id)
    logs = query.order_by(SystemLog.timestamp.desc()).limit(100).all()
    return jsonify([l.to_dict() for l in logs])
