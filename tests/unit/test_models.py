"""Unit tests for foundational model behavior."""

from __future__ import annotations

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import ApprovalStatus, MonthlyReport, User, UserRole


def test_user_password_hashing(app: Flask) -> None:
    """Password helpers should hash and verify credentials correctly."""

    with app.app_context():
        user = User(
            username="password_test",
            email="password_test@example.com",
            full_name="Password Test",
            role=UserRole.USER,
            is_active=True,
            is_approved=True,
        )
        user.set_password("securepass123")

        assert user.password_hash != "securepass123"
        assert user.check_password("securepass123") is True
        assert user.check_password("wrongpass") is False


def test_monthly_report_unique_constraint(app: Flask) -> None:
    """Monthly reports should enforce one record per user and month."""

    with app.app_context():
        user = User(
            username="report_user",
            email="report_user@example.com",
            full_name="Report User",
            role=UserRole.USER,
            is_active=True,
            is_approved=True,
        )
        user.set_password("securepass123")
        db.session.add(user)
        db.session.commit()

        first = MonthlyReport(
            user_id=user.id,
            year=2026,
            month=3,
            report_count=10,
            target_snapshot=5,
            approval_status=ApprovalStatus.APPROVED,
        )
        duplicate = MonthlyReport(
            user_id=user.id,
            year=2026,
            month=3,
            report_count=11,
            target_snapshot=5,
            approval_status=ApprovalStatus.APPROVED,
        )

        db.session.add(first)
        db.session.commit()

        db.session.add(duplicate)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
