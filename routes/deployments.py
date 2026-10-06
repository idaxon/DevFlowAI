from flask import Blueprint, render_template, jsonify, request
from database.models import Deployment
from tools.docker_tool import DockerTool
from config import Config

deployments_bp = Blueprint("deployments", __name__)

@deployments_bp.route("/deployments")
def deployments_view():
    deployments = Deployment.query.order_by(Deployment.created_at.desc()).all()
    return render_template("deployments.html", deployments=deployments, demo_mode=Config.DEMO_MODE)

@deployments_bp.route("/api/deployments", methods=["GET"])
def get_deployments_api():
    deployments = Deployment.query.order_by(Deployment.created_at.desc()).all()
    return jsonify([d.to_dict() for d in deployments])

@deployments_bp.route("/api/deployments/run", methods=["POST"])
def run_standalone_deployment():
    data = request.get_json() or {}
    tag = data.get("image", "devflow-standalone:latest")
    res = DockerTool.build_and_validate(Config.DEMO_REPO_DIR, tag=tag)
    return jsonify(res)
