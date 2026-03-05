"""
ME Statistics — Notifications Blueprint
==========================================
Bell badge notification system: JSON API for unread count,
recent items, mark as read.
"""
from flask import Blueprint

notifications_bp = Blueprint('notifications', __name__)

from app.notifications import routes  # noqa: E402, F401
