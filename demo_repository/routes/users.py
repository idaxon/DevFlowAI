from flask import Blueprint, jsonify
from database import get_users_from_db

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
def list_users():
    try:
        users = get_users_from_db()
        return jsonify({"users": users, "status": "ok"}), 200
    except RuntimeError as e:
        # Returns 500 when database is not connected
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
