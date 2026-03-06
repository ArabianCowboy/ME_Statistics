"""
ME Statistics — Model Tests
================================
Tests for data model creation, relationships, and constraints.
"""

import pytest
from app.models import (
    User, Goal, Task, MonthlyReport,
    AuditLog, Notification, SystemConfig,
)


class TestUserModel:
    """User model tests."""

    def test_create_user(self, db, admin_user):
        assert admin_user.id is not None
        assert admin_user.username == 'admin'
        assert admin_user.is_admin is True

    def test_user_is_admin_property(self, db, staff_user):
        assert staff_user.is_admin is False
        assert staff_user.role == 'user'

    def test_user_repr(self, db, admin_user):
        assert 'admin' in repr(admin_user)

    def test_unique_username(self, db, admin_user):
        """Duplicate usernames should raise an error."""
        import bcrypt
        pw = bcrypt.hashpw(b'x', bcrypt.gensalt()).decode('utf-8')
        dup = User(username='admin', email='dup@test.com',
                   full_name='Dup', password_hash=pw)
        db.session.add(dup)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_unique_email(self, db, admin_user):
        """Duplicate emails should raise an error."""
        import bcrypt
        pw = bcrypt.hashpw(b'x', bcrypt.gensalt()).decode('utf-8')
        dup = User(username='other', email='admin@test.com',
                   full_name='Dup', password_hash=pw)
        db.session.add(dup)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestGoalModel:
    """Goal model tests."""

    def test_create_goal(self, db, staff_user):
        goal = Goal(
            title='Complete Training',
            kpi='Hours completed',
            status='in_progress',
            progress=50,
            priority='high',
            user_id=staff_user.id,
            created_by_user_id=staff_user.id,
        )
        db.session.add(goal)
        db.session.commit()
        assert goal.id is not None
        assert goal.status == 'in_progress'

    def test_goal_owner_relationship(self, db, staff_user):
        goal = Goal(
            title='Test Goal', user_id=staff_user.id,
            created_by_user_id=staff_user.id,
        )
        db.session.add(goal)
        db.session.commit()
        assert goal.owner.id == staff_user.id


class TestTaskModel:
    """Task model tests."""

    def test_create_task(self, db, staff_user):
        task = Task(
            description='Review patient files',
            status='in_progress',
            progress=25,
            priority='high',
            user_id=staff_user.id,
        )
        db.session.add(task)
        db.session.commit()
        assert task.id is not None

    def test_task_defaults(self, db, staff_user):
        task = Task(description='Default task', user_id=staff_user.id)
        db.session.add(task)
        db.session.commit()
        assert task.status == 'not_started'
        assert task.progress == 0
        assert task.priority == 'medium'


class TestMonthlyReportModel:
    """Monthly report model tests."""

    def test_create_report(self, db, staff_user):
        report = MonthlyReport(
            user_id=staff_user.id,
            year=2026, month=3,
            report_count=15,
            target_snapshot=10,
        )
        db.session.add(report)
        db.session.commit()
        assert report.id is not None

    def test_unique_constraint(self, db, staff_user):
        """Only one report per user per month."""
        r1 = MonthlyReport(user_id=staff_user.id, year=2026, month=3,
                           report_count=10, target_snapshot=10)
        r2 = MonthlyReport(user_id=staff_user.id, year=2026, month=3,
                           report_count=15, target_snapshot=10)
        db.session.add(r1)
        db.session.commit()
        db.session.add(r2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestAuditLogModel:
    """AuditLog model tests."""

    def test_create_audit(self, db, admin_user):
        log = AuditLog(
            actor_user_id=admin_user.id,
            entity_type='user',
            entity_id=1,
            action='created',
        )
        db.session.add(log)
        db.session.commit()
        assert log.id is not None
        assert log.actor.id == admin_user.id

    def test_audit_with_json(self, db, admin_user):
        import json
        log = AuditLog(
            actor_user_id=admin_user.id,
            entity_type='system_config',
            entity_id=0,
            action='updated',
            before_json=json.dumps({'key': 'old'}),
            after_json=json.dumps({'key': 'new'}),
        )
        db.session.add(log)
        db.session.commit()
        assert 'old' in log.before_json
        assert 'new' in log.after_json


class TestNotificationModel:
    """Notification model tests."""

    def test_create_notification(self, db, staff_user):
        n = Notification(
            user_id=staff_user.id,
            type='approval_result',
            message='Your goal was approved.',
            link='/logs/goals',
        )
        db.session.add(n)
        db.session.commit()
        assert n.id is not None
        assert n.is_read is False


class TestSystemConfigModel:
    """SystemConfig model tests."""

    def test_get_set(self, db):
        SystemConfig.set('test_key', 'test_value')
        assert SystemConfig.get('test_key') == 'test_value'

    def test_get_default(self, db):
        assert SystemConfig.get('nonexistent', 'fallback') == 'fallback'

    def test_update_existing(self, db):
        SystemConfig.set('key1', 'v1')
        SystemConfig.set('key1', 'v2')
        assert SystemConfig.get('key1') == 'v2'

    def test_seed_defaults(self, db):
        SystemConfig.seed_defaults()
        assert SystemConfig.get('department_name') == 'Medication Error'
        assert SystemConfig.get('default_language') == 'en'
