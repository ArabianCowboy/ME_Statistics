"""
ME Statistics — Export Blueprint
===================================
Excel (.xlsx) data export for staff and admin.
"""
from flask import Blueprint

export_bp = Blueprint('export', __name__)

from app.export import routes  # noqa: E402, F401
