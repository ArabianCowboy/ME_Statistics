"""Helpers for persistent in-app notification creation."""

from __future__ import annotations

from typing import List, Optional

from app.extensions import db
from app.models import Notification, User, UserRole


def create_notification(
    user_id: int,
    notification_type: str,
    message: str,
    link: Optional[str] = None,
) -> Notification:
    """Create and stage a notification for one user.

    Args:
        user_id: Recipient user identifier.
        notification_type: Notification category.
        message: Human-readable notification content.
        link: Optional URL path for quick navigation.

    Returns:
        Notification: Staged notification model instance.

    Side Effects:
        Adds one notification row to the SQLAlchemy session.

    Raises:
        Any SQLAlchemy exception raised when session commits.
    """

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        link=link,
    )
    db.session.add(notification)
    return notification


def notify_admins(
    notification_type: str,
    message: str,
    link: Optional[str] = None,
) -> List[Notification]:
    """Create one notification for each active approved admin.

    Args:
        notification_type: Notification category.
        message: Human-readable notification content.
        link: Optional URL path for quick navigation.

    Returns:
        List[Notification]: List of staged notification instances.

    Side Effects:
        Adds multiple notification rows to SQLAlchemy session.

    Raises:
        Any SQLAlchemy exception raised when session commits.
    """

    admins = (
        User.query.filter_by(role=UserRole.ADMIN, is_active=True, is_approved=True)
        .order_by(User.id.asc())
        .all()
    )
    created: List[Notification] = []
    for admin in admins:
        created.append(
            create_notification(
                user_id=admin.id,
                notification_type=notification_type,
                message=message,
                link=link,
            )
        )
    return created
