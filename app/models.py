"""
ME Statistics — SQLAlchemy Models
==================================
All 7 data models as defined in the design document §4.
Models: User, Goal, Task, MonthlyReport, AuditLog, Notification, SystemConfig.
"""

from datetime import datetime
from flask_login import UserMixin
from app.extensions import db
import pytz


def _now_riyadh():
    """Current datetime in Asia/Riyadh timezone."""
    return datetime.now(pytz.timezone('Asia/Riyadh'))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.1 — User
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')  # 'admin' or 'user'
    preferred_lang = db.Column(db.String(2), nullable=False, default='en')  # 'en' or 'ar'
    monthly_target = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    # Per-user workflow toggles
    goal_approval_required = db.Column(db.Boolean, nullable=False, default=True)
    report_approval_required = db.Column(db.Boolean, nullable=False, default=False)
    can_create_goals = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh, onupdate=_now_riyadh)

    # ── Relationships ─────────────────────────────────────────
    goals = db.relationship('Goal', backref='owner', lazy='dynamic',
                            foreign_keys='Goal.user_id')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    monthly_reports = db.relationship('MonthlyReport', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.2 — Goal (Annual / Long-term)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    kpi = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='not_started')
    # Values: 'not_started', 'in_progress', 'completed'
    progress = db.Column(db.Integer, nullable=False, default=0)  # 0–100
    priority = db.Column(db.String(10), nullable=False, default='medium')
    # Values: 'high', 'medium', 'low'
    comments = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(10), nullable=False, default='approved')
    # Values: 'approved', 'pending', 'rejected'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh, onupdate=_now_riyadh)

    # ── Relationship for created_by ───────────────────────────
    creator = db.relationship('User', foreign_keys=[created_by_user_id],
                              backref='created_goals')

    def __repr__(self):
        return f'<Goal {self.id}: {self.title[:30]}>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.3 — Task (Short-term / Ad-hoc)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='not_started')
    progress = db.Column(db.Integer, nullable=False, default=0)
    priority = db.Column(db.String(10), nullable=False, default='medium')
    comments = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh, onupdate=_now_riyadh)

    def __repr__(self):
        return f'<Task {self.id}: {self.description[:30]}>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.4 — MonthlyReport (Statistical Data Report — SDR)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MonthlyReport(db.Model):
    __tablename__ = 'monthly_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1–12
    report_count = db.Column(db.Integer, nullable=False, default=0)
    target_snapshot = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(10), nullable=False, default='approved')
    # Values: 'approved', 'pending'

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh, onupdate=_now_riyadh)

    # Unique constraint: one report per user per month
    __table_args__ = (
        db.UniqueConstraint('user_id', 'year', 'month', name='uq_user_year_month'),
    )

    def __repr__(self):
        return f'<MonthlyReport {self.year}-{self.month:02d} user={self.user_id}>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.5 — AuditLog
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)
    # Values: 'user', 'goal', 'task', 'monthly_report', 'system_config'
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    # Values: 'created', 'updated', 'deactivated', 'approved', 'rejected', etc.
    before_json = db.Column(db.Text, nullable=True)
    after_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)
    # Immutable — no updated_at

    # ── Relationships ─────────────────────────────────────────
    actor = db.relationship('User', foreign_keys=[actor_user_id],
                            backref='audit_actions')
    target = db.relationship('User', foreign_keys=[target_user_id],
                             backref='audit_targets')

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}#{self.entity_id}>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.6 — Notification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    # Values: 'registration', 'approval_request', 'approval_result', 'goal_assigned'
    message = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh)

    def __repr__(self):
        return f'<Notification {self.type} → user={self.user_id}>'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.7 — SystemConfig
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now_riyadh, onupdate=_now_riyadh)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # ── Relationship ──────────────────────────────────────────
    updater = db.relationship('User', foreign_keys=[updated_by])

    @staticmethod
    def get(key, default=None):
        """Retrieve a config value by key, with optional default."""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def set(key, value, user_id=None):
        """Set or update a config value."""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.updated_by = user_id
        else:
            config = SystemConfig(key=key, value=str(value), updated_by=user_id)
            db.session.add(config)
        db.session.commit()
        return config

    # ── Default settings seed ─────────────────────────────────
    DEFAULTS = {
        'fiscal_year_start': '1',
        'default_language': 'en',
        'allow_self_registration': 'true',
        'leaderboard_visible': 'true',
        'default_monthly_target': '0',
        'department_name': 'Medication Error',
    }

    @classmethod
    def seed_defaults(cls):
        """Insert default settings if they don't already exist."""
        for key, value in cls.DEFAULTS.items():
            if not cls.query.filter_by(key=key).first():
                db.session.add(cls(key=key, value=value))
        db.session.commit()

    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'
