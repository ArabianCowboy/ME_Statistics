"""Integration tests for authentication and access decorators."""

from __future__ import annotations

from flask import Flask

from app.models import User, UserRole


def _login(client, username: str, password: str):
    """Submit login form for test scenarios.

    Args:
        client: Flask test client fixture.
        username: Account username to authenticate.
        password: Plain-text password.

    Returns:
        Response: Flask test response object.

    Side Effects:
        Creates authenticated session cookies on success.

    Raises:
        None.
    """

    return client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
            "remember_me": "y",
            "submit": "Sign in",
        },
        follow_redirects=True,
    )


def test_register_creates_pending_user(client, app: Flask) -> None:
    """Registration should create an unapproved active staff account."""

    response = client.post(
        "/auth/register",
        data={
            "full_name": "New Staff",
            "username": "newstaff",
            "email": "newstaff@example.com",
            "password": "newstaff123",
            "confirm_password": "newstaff123",
            "submit": "Create account",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="newstaff").first()
        assert user is not None
        assert user.is_active is True
        assert user.is_approved is False
        assert user.role == UserRole.USER


def test_unapproved_user_redirects_to_pending_page(client, pending_user: User) -> None:
    """Unapproved staff should land on pending approval page after login."""

    response = _login(client, username=pending_user.username, password="pendingpass123")

    assert response.status_code == 200
    assert b"Account pending approval" in response.data


def test_register_route_blocked_when_self_registration_disabled(app: Flask, client) -> None:
    """Registration route should return forbidden when feature is disabled."""

    app.config["ALLOW_SELF_REGISTRATION"] = False
    response = client.get("/auth/register")

    assert response.status_code == 403


def test_staff_cannot_access_admin_users_page(client, staff_user: User) -> None:
    """Staff accounts should be blocked from admin users page."""

    _login(client, username=staff_user.username, password="staffpass123")
    response = client.get("/users", follow_redirects=False)

    assert response.status_code == 403


def test_admin_can_access_admin_users_page(client, admin_user: User) -> None:
    """Admin accounts should access user management route."""

    _login(client, username=admin_user.username, password="adminpass123")
    response = client.get("/users", follow_redirects=False)

    assert response.status_code == 200


def test_failed_login_with_existing_user_returns_401(client, staff_user: User) -> None:
    """Existing user with wrong password should receive unauthorized response."""

    response = _login(client, username=staff_user.username, password="wrong-password")

    assert response.status_code == 401
