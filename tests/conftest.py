"""Shared pytest fixtures for application and database setup."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from flask import Flask

from app import create_app
from app.extensions import db
from app.models import LanguageCode, User, UserRole, seed_default_system_config


@pytest.fixture()
def app(tmp_path: Path) -> Generator[Flask, None, None]:
    """Create a test app with isolated SQLite database.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Generator[Flask, None, None]: Configured Flask app for test scope.

    Side Effects:
        Creates and tears down temporary database schema.

    Raises:
        Any SQLAlchemy exception raised while creating/dropping schema.
    """

    database_file = tmp_path / "test.db"
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_file}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "ALLOW_SELF_REGISTRATION": True,
    }

    test_app = create_app(test_config)

    with test_app.app_context():
        db.create_all()
        seed_default_system_config()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask):
    """Return Flask test client bound to test app.

    Args:
        app: Test application fixture.

    Returns:
        FlaskClient: Werkzeug test client instance.

    Side Effects:
        None.

    Raises:
        None.
    """

    return app.test_client()


@pytest.fixture()
def login(client):
    """Return helper function for posting login credentials in tests.

    Args:
        client: Flask test client fixture.

    Returns:
        callable: Function that submits login request and returns response.

    Side Effects:
        Creates authenticated test session cookies.

    Raises:
        None.
    """

    def _login(username: str, password: str):
        return client.post(
            "/auth/login",
            data={
                "username": username,
                "password": password,
                "submit": "Sign in",
            },
            follow_redirects=True,
        )

    return _login


@pytest.fixture()
def admin_user(app: Flask) -> User:
    """Insert and return an approved active admin user.

    Args:
        app: Test application fixture.

    Returns:
        User: Persisted admin user model.

    Side Effects:
        Writes one user row to the test database.

    Raises:
        Any SQLAlchemy exception raised during commit.
    """

    with app.app_context():
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            preferred_lang=LanguageCode.EN,
            is_active=True,
            is_approved=True,
        )
        user.set_password("adminpass123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture()
def staff_user(app: Flask) -> User:
    """Insert and return an approved active staff user.

    Args:
        app: Test application fixture.

    Returns:
        User: Persisted staff user model.

    Side Effects:
        Writes one user row to the test database.

    Raises:
        Any SQLAlchemy exception raised during commit.
    """

    with app.app_context():
        user = User(
            username="staff",
            email="staff@example.com",
            full_name="Staff User",
            role=UserRole.USER,
            preferred_lang=LanguageCode.EN,
            is_active=True,
            is_approved=True,
        )
        user.set_password("staffpass123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture()
def pending_user(app: Flask) -> User:
    """Insert and return an active user pending admin approval.

    Args:
        app: Test application fixture.

    Returns:
        User: Persisted pending staff model.

    Side Effects:
        Writes one user row to the test database.

    Raises:
        Any SQLAlchemy exception raised during commit.
    """

    with app.app_context():
        user = User(
            username="pending",
            email="pending@example.com",
            full_name="Pending Staff",
            role=UserRole.USER,
            preferred_lang=LanguageCode.EN,
            is_active=True,
            is_approved=False,
        )
        user.set_password("pendingpass123")
        db.session.add(user)
        db.session.commit()
        return user
