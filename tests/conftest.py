"""
ME Statistics — Test Configuration
=====================================
Shared pytest fixtures for the test suite.
"""

import pytest
import bcrypt
from app import create_app
from app.extensions import db as _db
from app.models import User, SystemConfig


@pytest.fixture(scope='session')
def app():
    """Create the Flask application for the test session."""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def db(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """A Flask test client with an active database."""
    return app.test_client()


@pytest.fixture
def admin_user(db):
    """Create and return an approved admin user."""
    pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    user = User(
        username='admin',
        email='admin@test.com',
        full_name='Test Admin',
        password_hash=pw,
        role='admin',
        is_active=True,
        is_approved=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def staff_user(db):
    """Create and return an approved staff user."""
    pw = bcrypt.hashpw(b'staff123', bcrypt.gensalt()).decode('utf-8')
    user = User(
        username='staff',
        email='staff@test.com',
        full_name='Test Staff',
        password_hash=pw,
        role='user',
        is_active=True,
        is_approved=True,
        monthly_target=10,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def pending_user(db):
    """Create and return a user pending approval."""
    pw = bcrypt.hashpw(b'pending123', bcrypt.gensalt()).decode('utf-8')
    user = User(
        username='pending',
        email='pending@test.com',
        full_name='Pending User',
        password_hash=pw,
        role='user',
        is_active=True,
        is_approved=False,
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username, password):
    """Helper to log in a user via the test client."""
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)
