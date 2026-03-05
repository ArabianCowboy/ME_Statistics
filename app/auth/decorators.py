"""Authorization decorators shared across protected routes."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import abort, flash, redirect, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, logout_user

from app.i18n import translate
from app.models import UserRole

ViewFunction = TypeVar("ViewFunction", bound=Callable[..., ResponseReturnValue])


def admin_required(view_func: ViewFunction) -> ViewFunction:
    """Allow access only to authenticated admin users.

    Args:
        view_func: Flask route handler to wrap.

    Returns:
        ViewFunction: Wrapped handler enforcing admin role checks.

    Side Effects:
        May abort with HTTP 403 response.

    Raises:
        werkzeug.exceptions.Forbidden: When current user is not an admin.
    """

    @wraps(view_func)
    def wrapped(*args: Any, **kwargs: Any) -> ResponseReturnValue:
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if current_user.role != UserRole.ADMIN:
            abort(403)

        return view_func(*args, **kwargs)

    return cast(ViewFunction, wrapped)


def active_required(view_func: ViewFunction) -> ViewFunction:
    """Allow access only to authenticated active users.

    Args:
        view_func: Flask route handler to wrap.

    Returns:
        ViewFunction: Wrapped handler enforcing active account checks.

    Side Effects:
        Logs the user out when account is inactive and adds a flash message.

    Raises:
        None.
    """

    @wraps(view_func)
    def wrapped(*args: Any, **kwargs: Any) -> ResponseReturnValue:
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if not current_user.is_active:
            logout_user()
            flash(translate("flash.account_inactive"), "error")
            return redirect(url_for("auth.login"))

        return view_func(*args, **kwargs)

    return cast(ViewFunction, wrapped)
