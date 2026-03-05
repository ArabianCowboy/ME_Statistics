"""
ME Statistics — User Management Routes
=========================================
Admin-only CRUD for user accounts.
Includes: list, create, edit (profile + toggles), deactivate, reactivate, reset password, approve.
"""

import json
import bcrypt
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.users import users_bp
from app.users.forms import CreateUserForm, EditUserForm, ResetPasswordForm
from app.models import User, AuditLog
from app.auth.decorators import admin_required


def _log_audit(entity_type, entity_id, action, before=None, after=None, target_user_id=None):
    """Helper to create an audit log entry."""
    entry = AuditLog(
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=json.dumps(before) if before else None,
        after_json=json.dumps(after) if after else None,
    )
    db.session.add(entry)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIST USERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/')
@login_required
@admin_required
def manage():
    """List all users with status indicators."""
    users = User.query.order_by(User.created_at.desc()).all()
    pending_count = User.query.filter_by(is_approved=False, is_active=True).count()
    return render_template('users/manage.html', users=users, pending_count=pending_count)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CREATE USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Admin creates a new user (pre-approved)."""
    form = CreateUserForm()
    if form.validate_on_submit():
        password_hash = bcrypt.hashpw(
            form.password.data.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            password_hash=password_hash,
            role=form.role.data,
            monthly_target=form.monthly_target.data,
            preferred_lang=form.preferred_lang.data,
            is_active=True,
            is_approved=True,  # Admin-created users are pre-approved
        )
        db.session.add(user)
        db.session.flush()

        _log_audit('user', user.id, 'created',
                    after={'username': user.username, 'role': user.role},
                    target_user_id=user.id)
        db.session.commit()
        flash(f'User "{user.username}" created successfully.', 'success')
        return redirect(url_for('users.manage'))

    return render_template('users/user_form.html', form=form, editing=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDIT USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """Edit user profile and per-user workflow toggles."""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user, original_email=user.email)

    if form.validate_on_submit():
        before = {
            'full_name': user.full_name, 'role': user.role,
            'monthly_target': user.monthly_target,
            'goal_approval_required': user.goal_approval_required,
            'report_approval_required': user.report_approval_required,
            'can_create_goals': user.can_create_goals,
        }

        # Guardrail: can't remove admin role from self
        if user.id == current_user.id and form.role.data != 'admin':
            flash('You cannot remove your own admin role.', 'error')
            return render_template('users/user_form.html', form=form, editing=True, user=user)

        # Guardrail: can't remove the last admin
        if user.role == 'admin' and form.role.data != 'admin':
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                flash('Cannot remove the last admin. Promote another user first.', 'error')
                return render_template('users/user_form.html', form=form, editing=True, user=user)

        user.full_name = form.full_name.data.strip()
        user.email = form.email.data.strip().lower()
        user.role = form.role.data
        user.monthly_target = form.monthly_target.data
        user.preferred_lang = form.preferred_lang.data
        user.goal_approval_required = form.goal_approval_required.data
        user.report_approval_required = form.report_approval_required.data
        user.can_create_goals = form.can_create_goals.data

        after = {
            'full_name': user.full_name, 'role': user.role,
            'monthly_target': user.monthly_target,
            'goal_approval_required': user.goal_approval_required,
            'report_approval_required': user.report_approval_required,
            'can_create_goals': user.can_create_goals,
        }
        _log_audit('user', user.id, 'updated', before=before, after=after,
                    target_user_id=user.id)
        db.session.commit()
        flash(f'User "{user.username}" updated successfully.', 'success')
        return redirect(url_for('users.manage'))

    return render_template('users/user_form.html', form=form, editing=True, user=user)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPROVE USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve(user_id):
    """Admin approves a pending user registration."""
    user = User.query.get_or_404(user_id)
    if user.is_approved:
        flash('User is already approved.', 'info')
        return redirect(url_for('users.manage'))

    user.is_approved = True
    _log_audit('user', user.id, 'approved', target_user_id=user.id)
    db.session.commit()
    flash(f'User "{user.username}" has been approved.', 'success')
    return redirect(url_for('users.manage'))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEACTIVATE / REACTIVATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate(user_id):
    """Soft-delete a user (preserve data)."""
    user = User.query.get_or_404(user_id)

    # Guardrail: can't deactivate yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('users.manage'))

    # Guardrail: can't deactivate the last admin
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('Cannot deactivate the last admin.', 'error')
            return redirect(url_for('users.manage'))

    user.is_active = False
    _log_audit('user', user.id, 'deactivated', target_user_id=user.id)
    db.session.commit()
    flash(f'User "{user.username}" has been deactivated.', 'success')
    return redirect(url_for('users.manage'))


@users_bp.route('/<int:user_id>/reactivate', methods=['POST'])
@login_required
@admin_required
def reactivate(user_id):
    """Restore a deactivated user."""
    user = User.query.get_or_404(user_id)
    user.is_active = True
    _log_audit('user', user.id, 'reactivated', target_user_id=user.id)
    db.session.commit()
    flash(f'User "{user.username}" has been reactivated.', 'success')
    return redirect(url_for('users.manage'))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESET PASSWORD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@users_bp.route('/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Admin resets a user's password."""
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        password_hash = bcrypt.hashpw(
            form.new_password.data.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        user.password_hash = password_hash
        _log_audit('user', user.id, 'password_reset', target_user_id=user.id)
        db.session.commit()
        flash(f'Password for "{user.username}" has been reset.', 'success')
        return redirect(url_for('users.manage'))

    return render_template('users/reset_password.html', form=form, user=user)
