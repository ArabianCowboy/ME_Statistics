"""
ME Statistics — Integration / Workflow Tests
================================================
Tests for multi-step workflows: user approval, report CRUD,
goal approval, backup operations, and health endpoint.
"""

import pytest
from tests.conftest import login
from app.models import User, MonthlyReport, Goal, AuditLog, SystemConfig


class TestUserApprovalWorkflow:
    """Admin approves a pending user → user can log in."""

    def test_approve_user(self, client, db, admin_user, pending_user):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/users/{pending_user.id}/approve',
                           follow_redirects=True)
        assert resp.status_code == 200
        updated = db.session.get(User, pending_user.id)
        assert updated.is_approved is True

    def test_deactivate_user(self, client, db, admin_user, staff_user):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/users/{staff_user.id}/deactivate',
                           follow_redirects=True)
        assert resp.status_code == 200
        updated = db.session.get(User, staff_user.id)
        assert updated.is_active is False


class TestMonthlyReportWorkflow:
    """Staff creates/updates a monthly report."""

    def test_create_report(self, client, db, staff_user):
        login(client, 'staff', 'staff123')
        resp = client.post('/logs/reports/new', data={
            'year': '2026',
            'month': '3',
            'report_count': '15',
            'notes': 'March stats',
        }, follow_redirects=True)
        assert resp.status_code == 200
        report = MonthlyReport.query.filter_by(
            user_id=staff_user.id, year=2026, month=3
        ).first()
        assert report is not None
        assert report.report_count == 15


class TestGoalWorkflow:
    """Staff creates goals, admin approves/rejects."""

    def test_create_goal(self, client, db, staff_user):
        login(client, 'staff', 'staff123')
        resp = client.post('/logs/goals/new', data={
            'title': 'Complete training program',
            'kpi': 'Hours completed',
            'priority': 'high',
        }, follow_redirects=True)
        assert resp.status_code == 200
        goal = Goal.query.filter_by(user_id=staff_user.id).first()
        assert goal is not None
        assert goal.title == 'Complete training program'


class TestSettingsWorkflow:
    """Admin updates system settings."""

    def test_update_settings(self, client, db, admin_user):
        login(client, 'admin', 'admin123')
        SystemConfig.seed_defaults()
        resp = client.post('/settings/', data={
            'department_name': 'Updated Dept',
            'default_monthly_target': '25',
            'fiscal_year_start': '1',
            'default_language': 'en',
            'allow_self_registration': 'y',
            'leaderboard_visible': 'y',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert SystemConfig.get('department_name') == 'Updated Dept'


class TestBackupWorkflow:
    """Admin runs manual backup."""

    def test_backup_page_loads(self, client, db, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.get('/settings/backups')
        assert resp.status_code == 200
        assert b'Backup' in resp.data

    def test_backup_config_save(self, client, db, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.post('/settings/backups/config', data={
            'auto_enabled': 'true',
            'interval_days': '3',
            'retention_count': '5',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert SystemConfig.get('backup_interval_days') == '3'
        assert SystemConfig.get('backup_retention_count') == '5'


class TestHealthEndpoint:
    """Health check endpoint."""

    def test_health(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        assert resp.json['status'] == 'ok'


class TestAuditLogViewer:
    """Audit log page loads and filters work."""

    def test_audit_page_loads(self, client, db, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.get('/settings/audit-log')
        assert resp.status_code == 200
        assert b'Audit' in resp.data

    def test_audit_filter(self, client, db, admin_user):
        login(client, 'admin', 'admin123')
        # Create a log entry
        log = AuditLog(
            actor_user_id=admin_user.id,
            entity_type='user', entity_id=1, action='created',
        )
        db.session.add(log)
        db.session.commit()
        resp = client.get('/settings/audit-log?entity=user')
        assert resp.status_code == 200
