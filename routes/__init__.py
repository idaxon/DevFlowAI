from routes.dashboard import dashboard_bp
from routes.repositories import repositories_bp
from routes.workflows import workflows_bp
from routes.agents import agents_bp
from routes.deployments import deployments_bp
from routes.logs import logs_bp
from routes.analytics import analytics_bp

__all__ = [
    "dashboard_bp",
    "repositories_bp",
    "workflows_bp",
    "agents_bp",
    "deployments_bp",
    "logs_bp",
    "analytics_bp",
]
