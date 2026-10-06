import os
from flask import Flask, jsonify
from config import Config
from database.db import db
from database.models import Repository, Workflow, SystemLog
from services.repository_service import RepositoryService
from routes import (
    dashboard_bp,
    repositories_bp,
    workflows_bp,
    agents_bp,
    deployments_bp,
    logs_bp,
    analytics_bp,
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.jinja_env.auto_reload = True

    # Initialize storage directories
    config_class.init_directories()

    # Initialize Database
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(repositories_bp)
    app.register_blueprint(workflows_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(deployments_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(analytics_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "status": 500}), 500

    # Initialize database tables and demo seed data
    with app.app_context():
        db.create_all()
        # Seed demo repo
        RepositoryService.register_or_get_demo_repo()

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
