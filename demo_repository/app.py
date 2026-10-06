import os
from flask import Flask, jsonify
from config import Config
from database import init_db
from routes.users import users_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    init_db(app)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/users")

    @app.route("/")
    def index():
        return jsonify({"service": "Flask Demo API", "status": "running"})

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "code": 200})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
