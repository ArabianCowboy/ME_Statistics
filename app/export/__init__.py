"""Export blueprint registration."""

from flask import Blueprint

export_bp = Blueprint("export", __name__, url_prefix="/export")

from app.export import routes  # noqa: E402,F401
