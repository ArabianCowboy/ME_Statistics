"""
ME Statistics — Auth Decorators
================================
Custom access control decorators for route protection.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required  # noqa: F401 — re-export


def admin_required(f):
    """
    Decorator: User must be logged in AND have role='admin'.
    Returns 403 Forbidden otherwise.
    """
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def active_required(f):
    """
    Decorator: User must be logged in, active, AND approved.
    Redirects to a pending-approval page if not approved.
    """
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_approved:
            return redirect(url_for('auth.pending_approval'))
        return f(*args, **kwargs)
    return decorated
