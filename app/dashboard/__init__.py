"""Dashboard page and API blueprint registration."""

from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.dashboard import routes  # noqa: E402,F401
