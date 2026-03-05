"""
ME Statistics — Users Blueprint
=================================
Admin user management.
"""
from flask import Blueprint

users_bp = Blueprint('users', __name__, template_folder='../templates/users')

from app.users import routes  # noqa: E402, F401 — register route handlers
