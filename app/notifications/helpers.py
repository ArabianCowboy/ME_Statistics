"""
ME Statistics — Notification Helpers
=======================================
Reusable function to create notifications across blueprints.
"""

from app.extensions import db
from app.models import Notification, User


def create_notification(user_id, notif_type, message, link=None):
    """Create a notification for a specific user.

    Args:
        user_id: Target user ID
        notif_type: 'registration', 'approval_request', 'approval_result', 'goal_assigned'
        message: Notification text
        link: Optional URL to navigate to
    """
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        message=message,
        link=link,
    )
    db.session.add(notif)
    return notif


def notify_all_admins(notif_type, message, link=None):
    """Create a notification for all active admin users.

    Args:
        notif_type: Notification type
        message: Notification text
        link: Optional URL
    """
    admins = User.query.filter_by(role='admin', is_active=True, is_approved=True).all()
    for admin in admins:
        create_notification(admin.id, notif_type, message, link)
