"""Route handlers for login, registration, and logout flows."""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.extensions import db
from app.i18n import translate
from app.models import User, UserRole
from app.services.audit import log_mutation, model_to_dict
from app.services.notifications import notify_admins


def _is_safe_next_url(next_url: str) -> bool:
    """Validate untrusted `next` URLs to prevent open redirects.

    Args:
        next_url: URL value provided in query params.

    Returns:
        bool: `True` when URL points to this site.

    Side Effects:
        None.

    Raises:
        None.
    """

    if not next_url:
        return False

    parsed = urlsplit(next_url)
    return parsed.scheme == "" and parsed.netloc == ""


def _post_login_redirect(user: User) -> ResponseReturnValue:
    """Resolve the correct post-login destination for a user.

    Args:
        user: Authenticated user instance.

    Returns:
        ResponseReturnValue: Redirect response to the appropriate page.

    Side Effects:
        None.

    Raises:
        None.
    """

    if not user.is_approved and user.role != UserRole.ADMIN:
        return redirect(url_for("auth.pending_approval"))

    if user.role == UserRole.ADMIN:
        return redirect(url_for("dashboard.admin_dashboard"))

    return redirect(url_for("dashboard.staff_dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Authenticate an existing user and create a login session.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered login page or redirect after success.

    Side Effects:
        Creates Flask-Login session cookies and reads database user records.

    Raises:
        None.
    """

    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        username = str(form.username.data or "").strip()
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(str(form.password.data or "")):
            if user is not None:
                try:
                    log_mutation(
                        actor_user_id=user.id,
                        entity_type="user",
                        entity_id=user.id,
                        action="login_failed",
                        before_state=model_to_dict(user),
                        after_state=None,
                        target_user_id=user.id,
                    )
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()

            flash(translate("flash.invalid_credentials"), "error")
            return render_template("auth/login.html", form=form), 401

        if not user.is_active:
            flash(translate("flash.account_inactive"), "error")
            return render_template("auth/login.html", form=form), 403

        login_user(user, remember=form.remember_me.data)
        flash(translate("flash.login_success"), "success")

        next_url = request.args.get("next", "")
        if _is_safe_next_url(next_url):
            return redirect(next_url)

        return _post_login_redirect(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> ResponseReturnValue:
    """Create a new user account with pending admin approval.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered registration page or redirect to login.

    Side Effects:
        Inserts a new user row when registration succeeds.

    Raises:
        werkzeug.exceptions.Forbidden: When self-registration is disabled.
    """

    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    if not current_app.config.get("ALLOW_SELF_REGISTRATION", True):
        abort(403)

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=str(form.username.data or "").strip(),
            email=str(form.email.data or "").strip().lower(),
            full_name=str(form.full_name.data or "").strip(),
            role=UserRole.USER,
            is_active=True,
            is_approved=False,
        )
        user.set_password(str(form.password.data or ""))

        try:
            db.session.add(user)
            db.session.flush()
            log_mutation(
                actor_user_id=user.id,
                entity_type="user",
                entity_id=user.id,
                action="created",
                before_state=None,
                after_state=model_to_dict(user),
                target_user_id=user.id,
            )
            notify_admins(
                notification_type="registration",
                message=translate("notification.new_registration", name=user.full_name),
                link=url_for("users.manage_users"),
            )
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(translate("flash.register_failed"), "error")
            return render_template("auth/register.html", form=form), 500

        flash(translate("flash.register_success"), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> ResponseReturnValue:
    """Terminate the current user's session.

    Args:
        None.

    Returns:
        ResponseReturnValue: Redirect to login page.

    Side Effects:
        Removes the active Flask-Login session.

    Raises:
        None.
    """

    logout_user()
    flash(translate("flash.logged_out"), "info")
    return redirect(url_for("auth.login"))


@auth_bp.get("/pending-approval")
@login_required
def pending_approval() -> ResponseReturnValue:
    """Show waiting page for users who need admin approval.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered pending approval page or redirect.

    Side Effects:
        None.

    Raises:
        None.
    """

    if current_user.is_approved or current_user.role == UserRole.ADMIN:
        return _post_login_redirect(current_user)

    return render_template("auth/pending_approval.html")
