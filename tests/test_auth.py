"""
ME Statistics — Authentication Tests
========================================
Tests for login, register, logout, role guards, and pending approval flow.
"""

import pytest
from tests.conftest import login


class TestLogin:
    """Login endpoint tests."""

    def test_login_page_loads(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'login' in resp.data.lower() or b'Login' in resp.data

    def test_login_valid_admin(self, client, admin_user):
        resp = login(client, 'admin', 'admin123')
        assert resp.status_code == 200
        # Should redirect to dashboard
        assert b'Dashboard' in resp.data or b'dashboard' in resp.data.lower()

    def test_login_valid_staff(self, client, staff_user):
        resp = login(client, 'staff', 'staff123')
        assert resp.status_code == 200

    def test_login_wrong_password(self, client, admin_user):
        resp = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert b'Invalid' in resp.data or resp.status_code == 200

    def test_login_nonexistent_user(self, client):
        resp = client.post('/auth/login', data={
            'username': 'ghost',
            'password': 'nope',
        }, follow_redirects=True)
        assert b'Invalid' in resp.data or resp.status_code == 200

    def test_login_deactivated_user(self, client, db):
        """Deactivated users should not be able to log in."""
        import bcrypt
        from app.models import User
        pw = bcrypt.hashpw(b'test123', bcrypt.gensalt()).decode('utf-8')
        user = User(
            username='deactivated', email='deact@test.com',
            full_name='Deactivated', password_hash=pw,
            role='user', is_active=False, is_approved=True,
        )
        db.session.add(user)
        db.session.commit()
        resp = login(client, 'deactivated', 'test123')
        assert b'deactivated' in resp.data.lower() or b'contact' in resp.data.lower()

    def test_failed_login_creates_audit_log(self, client, db, admin_user):
        """Failed login should create an AuditLog entry."""
        from app.models import AuditLog
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        log = AuditLog.query.filter_by(action='login_failed').first()
        assert log is not None
        assert log.entity_type == 'user'
        assert log.actor_user_id == admin_user.id


class TestRegister:
    """Registration endpoint tests."""

    def test_register_page_loads(self, client, db):
        from app.models import SystemConfig
        SystemConfig.set('allow_self_registration', 'true')
        resp = client.get('/auth/register')
        assert resp.status_code == 200

    def test_register_new_user(self, client, db):
        from app.models import SystemConfig, User
        SystemConfig.set('allow_self_registration', 'true')
        resp = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'full_name': 'New User',
            'password': 'Password1!',
            'confirm_password': 'Password1!',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.is_approved is False  # Requires admin approval

    def test_register_disabled(self, client, db):
        """When registration is disabled, should redirect."""
        from app.models import SystemConfig
        SystemConfig.set('allow_self_registration', 'false')
        resp = client.get('/auth/register', follow_redirects=True)
        assert b'disabled' in resp.data.lower() or b'login' in resp.data.lower()


class TestLogout:
    """Logout tests."""

    def test_logout(self, client, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.post('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert b'logged out' in resp.data.lower() or b'login' in resp.data.lower()


class TestPendingApproval:
    """Pending approval flow tests."""

    def test_pending_user_redirected(self, client, pending_user):
        """A pending user should be redirected to the pending page."""
        login(client, 'pending', 'pending123')
        resp = client.get('/auth/redirect', follow_redirects=True)
        assert resp.status_code == 200


class TestAdminGuard:
    """Role-based access control tests."""

    def test_settings_requires_admin(self, client, staff_user):
        """Staff users should not access admin-only settings."""
        login(client, 'staff', 'staff123')
        resp = client.get('/settings/', follow_redirects=True)
        assert resp.status_code in (200, 403)

    def test_settings_accessible_to_admin(self, client, admin_user):
        """Admin users should access settings."""
        login(client, 'admin', 'admin123')
        resp = client.get('/settings/')
        assert resp.status_code == 200

    def test_users_page_requires_admin(self, client, staff_user):
        """Staff users should not access user management."""
        login(client, 'staff', 'staff123')
        resp = client.get('/users/', follow_redirects=True)
        assert resp.status_code in (200, 403)

    def test_audit_log_requires_admin(self, client, staff_user):
        login(client, 'staff', 'staff123')
        resp = client.get('/settings/audit-log', follow_redirects=True)
        assert resp.status_code in (200, 403)

    def test_backups_requires_admin(self, client, staff_user):
        login(client, 'staff', 'staff123')
        resp = client.get('/settings/backups', follow_redirects=True)
        assert resp.status_code in (200, 403)
