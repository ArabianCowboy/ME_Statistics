"""Route handlers for admin user management, settings, and notifications."""

from __future__ import annotations

from typing import Dict

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.auth.decorators import active_required, admin_required
from app.extensions import db
from app.i18n import translate
from app.models import LanguageCode, Notification, User, UserRole
from app.services.audit import log_mutation, model_to_dict
from app.services.system_config import get_config_map, set_config_values
from app.users import users_bp
from app.users.forms import ResetPasswordForm, SystemSettingsForm, UserCreateForm, UserEditForm


def _active_admin_count() -> int:
    """Count active approved administrator accounts.

    Args:
        None.

    Returns:
        int: Number of active approved admin users.

    Side Effects:
        Executes database read query.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    return User.query.filter_by(
        role=UserRole.ADMIN,
        is_active=True,
        is_approved=True,
    ).count()


def _settings_updates_from_form(form: SystemSettingsForm) -> Dict[str, str]:
    """Convert settings form values into persisted key-value pairs.

    Args:
        form: Submitted system settings form.

    Returns:
        Dict[str, str]: Stringified key-value pairs for persistence.

    Side Effects:
        None.

    Raises:
        None.
    """

    return {
        "fiscal_year_start": str(form.fiscal_year_start.data),
        "default_language": str(form.default_language.data),
        "allow_self_registration": "true" if form.allow_self_registration.data else "false",
        "leaderboard_visible": "true" if form.leaderboard_visible.data else "false",
        "default_monthly_target": str(form.default_monthly_target.data),
        "department_name": str(form.department_name.data),
    }


@users_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
@login_required
@active_required
@admin_required
def manage_users() -> ResponseReturnValue:
    """Render user management page and handle admin-driven user creation.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered page or redirect after successful create.

    Side Effects:
        Writes new `User` rows and corresponding `AuditLog` entries.

    Raises:
        None. Failures are handled with flash messages.
    """

    form = UserCreateForm()
    reset_form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User(
            username=str(form.username.data or "").strip(),
            email=str(form.email.data or "").strip().lower(),
            full_name=str(form.full_name.data or "").strip(),
            role=UserRole(str(form.role.data)),
            preferred_lang=LanguageCode.EN,
            monthly_target=int(form.monthly_target.data or 0),
            is_active=True,
            is_approved=bool(form.is_approved.data),
            goal_approval_required=bool(form.goal_approval_required.data),
            report_approval_required=bool(form.report_approval_required.data),
            can_create_goals=bool(form.can_create_goals.data),
        )
        if user.role == UserRole.ADMIN:
            user.is_approved = True

        user.set_password(str(form.password.data or ""))

        try:
            db.session.add(user)
            db.session.flush()
            log_mutation(
                actor_user_id=current_user.id,
                entity_type="user",
                entity_id=user.id,
                action="created",
                before_state=None,
                after_state=model_to_dict(user),
                target_user_id=user.id,
            )
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(translate("flash.user_create_failed"), "error")
        else:
            flash(translate("flash.user_created", full_name=user.full_name), "success")
            return redirect(url_for("users.manage_users"))

    users = User.query.order_by(User.created_at.desc(), User.id.desc()).all()
    return render_template(
        "users/manage.html",
        form=form,
        reset_form=reset_form,
        users=users,
    )


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@active_required
@admin_required
def edit_user(user_id: int) -> ResponseReturnValue:
    """Render and process profile updates for one user.

    Args:
        user_id: Target user identifier.

    Returns:
        ResponseReturnValue: Rendered edit page or redirect on success.

    Side Effects:
        Updates user fields and writes audit entries.

    Raises:
        werkzeug.exceptions.NotFound: When user does not exist.
    """

    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    form.user_id.data = str(user.id)

    if form.validate_on_submit():
        requested_role = UserRole(str(form.role.data))

        if user.id == current_user.id and requested_role != UserRole.ADMIN:
            flash(translate("flash.cannot_demote_self"), "error")
            return redirect(url_for("users.edit_user", user_id=user.id))

        if (
            user.role == UserRole.ADMIN
            and requested_role != UserRole.ADMIN
            and _active_admin_count() <= 1
        ):
            flash(translate("flash.cannot_remove_last_admin"), "error")
            return redirect(url_for("users.edit_user", user_id=user.id))

        before_state = model_to_dict(user)
        user.username = str(form.username.data or "").strip()
        user.email = str(form.email.data or "").strip().lower()
        user.full_name = str(form.full_name.data or "").strip()
        user.role = requested_role
        user.preferred_lang = LanguageCode(str(form.preferred_lang.data))
        user.monthly_target = int(form.monthly_target.data or 0)
        user.is_approved = bool(form.is_approved.data)
        user.goal_approval_required = bool(form.goal_approval_required.data)
        user.report_approval_required = bool(form.report_approval_required.data)
        user.can_create_goals = bool(form.can_create_goals.data)

        password_value = str(form.new_password.data or "").strip()
        if password_value:
            user.set_password(password_value)

        if user.role == UserRole.ADMIN:
            user.is_approved = True

        try:
            log_mutation(
                actor_user_id=current_user.id,
                entity_type="user",
                entity_id=user.id,
                action="updated",
                before_state=before_state,
                after_state=model_to_dict(user),
                target_user_id=user.id,
            )
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(translate("flash.user_update_failed"), "error")
        else:
            flash(translate("flash.user_updated", full_name=user.full_name), "success")
            return redirect(url_for("users.edit_user", user_id=user.id))

    return render_template("users/edit.html", form=form, user=user)


@users_bp.post("/<int:user_id>/deactivate")
@login_required
@active_required
@admin_required
def deactivate_user(user_id: int) -> ResponseReturnValue:
    """Soft deactivate a user account while preserving historical records.

    Args:
        user_id: Target user identifier.

    Returns:
        ResponseReturnValue: Redirect to management page.

    Side Effects:
        Updates `is_active` flag and writes an audit entry.

    Raises:
        werkzeug.exceptions.NotFound: When user does not exist.
    """

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash(translate("flash.cannot_deactivate_self"), "error")
        return redirect(url_for("users.manage_users"))

    if user.role == UserRole.ADMIN and user.is_active and _active_admin_count() <= 1:
        flash(translate("flash.cannot_remove_last_admin"), "error")
        return redirect(url_for("users.manage_users"))

    before_state = model_to_dict(user)
    user.is_active = False

    try:
        log_mutation(
            actor_user_id=current_user.id,
            entity_type="user",
            entity_id=user.id,
            action="deactivated",
            before_state=before_state,
            after_state=model_to_dict(user),
            target_user_id=user.id,
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(translate("flash.user_deactivate_failed"), "error")
    else:
        flash(translate("flash.user_deactivated", full_name=user.full_name), "warning")

    return redirect(url_for("users.manage_users"))


@users_bp.post("/<int:user_id>/reactivate")
@login_required
@active_required
@admin_required
def reactivate_user(user_id: int) -> ResponseReturnValue:
    """Reactivate a previously deactivated user account.

    Args:
        user_id: Target user identifier.

    Returns:
        ResponseReturnValue: Redirect to management page.

    Side Effects:
        Updates `is_active` and writes audit entry.

    Raises:
        werkzeug.exceptions.NotFound: When user does not exist.
    """

    user = User.query.get_or_404(user_id)
    before_state = model_to_dict(user)
    user.is_active = True

    try:
        log_mutation(
            actor_user_id=current_user.id,
            entity_type="user",
            entity_id=user.id,
            action="reactivated",
            before_state=before_state,
            after_state=model_to_dict(user),
            target_user_id=user.id,
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(translate("flash.user_reactivate_failed"), "error")
    else:
        flash(translate("flash.user_reactivated", full_name=user.full_name), "success")

    return redirect(url_for("users.manage_users"))


@users_bp.post("/<int:user_id>/reset-password")
@login_required
@active_required
@admin_required
def reset_password(user_id: int) -> ResponseReturnValue:
    """Reset an account password as an admin action.

    Args:
        user_id: Target user identifier.

    Returns:
        ResponseReturnValue: Redirect to user management page.

    Side Effects:
        Updates password hash and writes audit entry.

    Raises:
        werkzeug.exceptions.NotFound: When user does not exist.
    """

    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if not form.validate_on_submit():
        flash(translate("flash.invalid_password"), "error")
        return redirect(url_for("users.manage_users"))

    before_state = model_to_dict(user)
    user.set_password(str(form.password.data or ""))

    try:
        log_mutation(
            actor_user_id=current_user.id,
            entity_type="user",
            entity_id=user.id,
            action="password_reset",
            before_state=before_state,
            after_state=model_to_dict(user),
            target_user_id=user.id,
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(translate("flash.password_reset_failed"), "error")
    else:
        flash(translate("flash.password_reset_success", full_name=user.full_name), "success")

    return redirect(url_for("users.manage_users"))


@users_bp.route("/settings", methods=["GET", "POST"])
@login_required
@active_required
@admin_required
def system_settings() -> ResponseReturnValue:
    """Display and persist application-wide system configuration values.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered settings page or redirect on success.

    Side Effects:
        Writes key-value system configuration rows and audit entries.

    Raises:
        None.
    """

    form = SystemSettingsForm()
    config_map = get_config_map()

    if request.method == "GET":
        form.fiscal_year_start.data = config_map.get("fiscal_year_start", "1")
        form.default_language.data = config_map.get("default_language", "en")
        form.allow_self_registration.data = (
            config_map.get("allow_self_registration", "true") == "true"
        )
        form.leaderboard_visible.data = config_map.get("leaderboard_visible", "true") == "true"
        form.default_monthly_target.data = int(
            config_map.get("default_monthly_target", "0")
        )
        form.department_name.data = config_map.get("department_name", "Medication Error")
        return render_template("users/settings.html", form=form)

    if form.validate_on_submit():
        try:
            updates = _settings_updates_from_form(form)
            changes = set_config_values(updates=updates, actor_user_id=current_user.id)

            for changed_key, state in changes.items():
                log_mutation(
                    actor_user_id=current_user.id,
                    entity_type="system_config",
                    entity_id=0,
                    action=f"updated_{changed_key}",
                    before_state={"value": state["before"]},
                    after_state={"value": state["after"]},
                    target_user_id=current_user.id,
                )

            db.session.commit()
            current_app.config["ALLOW_SELF_REGISTRATION"] = (
                updates["allow_self_registration"] == "true"
            )
        except SQLAlchemyError:
            db.session.rollback()
            flash(translate("flash.settings_update_failed"), "error")
        else:
            flash(translate("flash.settings_updated"), "success")
            return redirect(url_for("users.system_settings"))

    return render_template("users/settings.html", form=form)


@users_bp.post("/notifications/<int:notification_id>/read")
@login_required
@active_required
def mark_notification_read(notification_id: int) -> ResponseReturnValue:
    """Mark one notification as read for the current user.

    Args:
        notification_id: Notification identifier.

    Returns:
        ResponseReturnValue: Redirect back to referrer or dashboard.

    Side Effects:
        Updates one notification row.

    Raises:
        werkzeug.exceptions.NotFound: When notification does not belong to user.
    """

    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(404)

    notification.is_read = True
    db.session.commit()

    fallback = (
        url_for("dashboard.admin_dashboard")
        if current_user.is_admin
        else url_for("dashboard.staff_dashboard")
    )
    return redirect(request.referrer or fallback)


@users_bp.post("/notifications/read-all")
@login_required
@active_required
def mark_all_notifications_read() -> ResponseReturnValue:
    """Mark all unread notifications as read for the current user.

    Args:
        None.

    Returns:
        ResponseReturnValue: Redirect back to referrer or dashboard.

    Side Effects:
        Updates all unread notification rows for current user.

    Raises:
        Any SQLAlchemy exception during commit.
    """

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
    ).all()

    for notification in unread_notifications:
        notification.is_read = True

    db.session.commit()

    fallback = (
        url_for("dashboard.admin_dashboard")
        if current_user.is_admin
        else url_for("dashboard.staff_dashboard")
    )
    return redirect(request.referrer or fallback)
