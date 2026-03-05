"""
ME Statistics — Notification Routes
=======================================
JSON API endpoints for the bell badge notification system.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.notifications import notifications_bp
from app.models import Notification


@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Return unread count + recent notifications for the current user."""
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    recent = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(15).all()

    items = []
    for n in recent:
        items.append({
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %H:%M'),
        })

    return jsonify({
        'unread_count': unread_count,
        'notifications': items,
    })


@notifications_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    """Mark a single notification as read."""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'ok': True})


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user."""
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})
