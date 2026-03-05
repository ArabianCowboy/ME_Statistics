"""Database models and domain constants for the ME Statistics application."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Dict

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

from app.extensions import bcrypt, db


class UserRole(str, enum.Enum):
    """Bounded role values for authorization decisions."""

    ADMIN = "admin"
    USER = "user"


class LanguageCode(str, enum.Enum):
    """Supported user language values."""

    EN = "en"
    AR = "ar"


class WorkStatus(str, enum.Enum):
    """Progress states shared by goals and tasks."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PriorityLevel(str, enum.Enum):
    """Priority values used by goals and tasks."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalStatus(str, enum.Enum):
    """Approval states for moderated entities."""

    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class TimestampMixin:
    """Reusable created/updated timestamp columns."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(UserMixin, TimestampMixin, db.Model):
    """Authenticated user record with profile and workflow preferences."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(
        db.Enum(UserRole, native_enum=False, length=16),
        nullable=False,
        default=UserRole.USER,
    )
    preferred_lang = db.Column(
        db.Enum(LanguageCode, native_enum=False, length=8),
        nullable=False,
        default=LanguageCode.EN,
    )
    monthly_target = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    goal_approval_required = db.Column(db.Boolean, nullable=False, default=True)
    report_approval_required = db.Column(db.Boolean, nullable=False, default=False)
    can_create_goals = db.Column(db.Boolean, nullable=False, default=True)

    goals = db.relationship(
        "Goal",
        foreign_keys="Goal.user_id",
        back_populates="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    created_goals = db.relationship(
        "Goal",
        foreign_keys="Goal.created_by_user_id",
        back_populates="creator",
        lazy="dynamic",
    )
    tasks = db.relationship(
        "Task",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    monthly_reports = db.relationship(
        "MonthlyReport",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    actor_audit_logs = db.relationship(
        "AuditLog",
        foreign_keys="AuditLog.actor_user_id",
        back_populates="actor",
        lazy="dynamic",
    )
    target_audit_logs = db.relationship(
        "AuditLog",
        foreign_keys="AuditLog.target_user_id",
        back_populates="target_user",
        lazy="dynamic",
    )
    updated_system_configs = db.relationship(
        "SystemConfig",
        foreign_keys="SystemConfig.updated_by",
        back_populates="updated_by_user",
        lazy="dynamic",
    )

    @property
    def is_admin(self) -> bool:
        """Check whether this user has administrator role.

        Args:
            None.

        Returns:
            bool: `True` when role is admin, otherwise `False`.

        Side Effects:
            None.

        Raises:
            None.
        """

        return self.role == UserRole.ADMIN

    def set_password(self, password: str) -> None:
        """Hash and store a plain-text password.

        Args:
            password: Plain-text password from a trusted form input.

        Returns:
            None.

        Side Effects:
            Mutates `password_hash` on the current instance.

        Raises:
            ValueError: When password is empty.
        """

        if not password:
            raise ValueError("Password must not be empty.")
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a plain-text password against the stored hash.

        Args:
            password: Plain-text password to verify.

        Returns:
            bool: `True` when the password matches.

        Side Effects:
            None.

        Raises:
            None.
        """

        if not password:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        """Return an unambiguous debug representation.

        Args:
            None.

        Returns:
            str: Lightweight identifier for logs and debugging.

        Side Effects:
            None.

        Raises:
            None.
        """

        return f"<User id={self.id} username={self.username!r} role={self.role.value!r}>"


class Goal(TimestampMixin, db.Model):
    """Annual or long-term user objective with optional approval flow."""

    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    kpi = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(WorkStatus, native_enum=False, length=16),
        nullable=False,
        default=WorkStatus.NOT_STARTED,
    )
    progress = db.Column(db.Integer, nullable=False, default=0)
    priority = db.Column(
        db.Enum(PriorityLevel, native_enum=False, length=16),
        nullable=False,
        default=PriorityLevel.MEDIUM,
    )
    comments = db.Column(db.Text, nullable=True)
    approval_status = db.Column(
        db.Enum(ApprovalStatus, native_enum=False, length=16),
        nullable=False,
        default=ApprovalStatus.APPROVED,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    owner = db.relationship("User", foreign_keys=[user_id], back_populates="goals")
    creator = db.relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_goals",
    )


class Task(TimestampMixin, db.Model):
    """Short-term task assigned to a staff member."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(WorkStatus, native_enum=False, length=16),
        nullable=False,
        default=WorkStatus.NOT_STARTED,
    )
    progress = db.Column(db.Integer, nullable=False, default=0)
    priority = db.Column(
        db.Enum(PriorityLevel, native_enum=False, length=16),
        nullable=False,
        default=PriorityLevel.MEDIUM,
    )
    comments = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="tasks")


class MonthlyReport(TimestampMixin, db.Model):
    """Monthly report count snapshot for one user and month."""

    __tablename__ = "monthly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_monthly_report_period"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    report_count = db.Column(db.Integer, nullable=False)
    target_snapshot = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    approval_status = db.Column(
        db.Enum(ApprovalStatus, native_enum=False, length=16),
        nullable=False,
        default=ApprovalStatus.APPROVED,
    )

    user = db.relationship("User", back_populates="monthly_reports")


class AuditLog(db.Model):
    """Immutable audit trail for data mutations."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    entity_type = db.Column(db.String(64), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(64), nullable=False)
    before_json = db.Column(db.Text, nullable=True)
    after_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    actor = db.relationship("User", foreign_keys=[actor_user_id], back_populates="actor_audit_logs")
    target_user = db.relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="target_audit_logs",
    )


class Notification(db.Model):
    """Persistent notification item for the bell badge workflow."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(64), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")


class SystemConfig(db.Model):
    """Runtime key-value settings managed by administrators."""

    __tablename__ = "system_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    updated_by_user = db.relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="updated_system_configs",
    )


DEFAULT_SYSTEM_CONFIG: Dict[str, str] = {
    "fiscal_year_start": "1",
    "default_language": "en",
    "allow_self_registration": "true",
    "leaderboard_visible": "true",
    "default_monthly_target": "0",
    "department_name": "Medication Error",
}


def seed_default_system_config() -> None:
    """Insert default system config keys when they do not exist.

    Args:
        None.

    Returns:
        None.

    Side Effects:
        Writes rows to `system_config` and commits the active database session.

    Raises:
        Any SQLAlchemy exception raised during write or commit operations.
    """

    existing_keys = {
        row[0]
        for row in db.session.query(SystemConfig.key).all()
    }
    has_new_records = False

    for key, value in DEFAULT_SYSTEM_CONFIG.items():
        if key not in existing_keys:
            db.session.add(SystemConfig(key=key, value=value))
            has_new_records = True

    if has_new_records:
        db.session.commit()
