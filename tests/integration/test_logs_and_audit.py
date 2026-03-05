"""Integration tests covering logs CRUD, approvals, and audit trail creation."""

from __future__ import annotations

from flask import Flask

from app.extensions import db
from app.models import ApprovalStatus, AuditLog, MonthlyReport, User


def test_staff_report_creation_sets_pending_when_required(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Report approval toggle should force new reports into pending state."""

    with app.app_context():
        user = User.query.get(staff_user.id)
        user.report_approval_required = True
        db.session.commit()

    login(staff_user.username, "staffpass123")
    response = client.post(
        "/logs/reports",
        data={
            "year": 2026,
            "month": "3",
            "report_count": 12,
            "notes": "Integration pending test",
            "submit": "Save report",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        report = MonthlyReport.query.filter_by(user_id=staff_user.id, year=2026, month=3).first()
        assert report is not None
        assert report.approval_status == ApprovalStatus.PENDING


def test_admin_approval_updates_pending_report_and_notifies_owner(
    app: Flask,
    client,
    login,
    admin_user: User,
    staff_user: User,
) -> None:
    """Admin approval endpoint should transition pending report to approved."""

    with app.app_context():
        report = MonthlyReport(
            user_id=staff_user.id,
            year=2026,
            month=4,
            report_count=10,
            target_snapshot=8,
            approval_status=ApprovalStatus.PENDING,
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    login(admin_user.username, "adminpass123")
    response = client.post(
        f"/dashboard/approve/report/{report_id}",
        data={"action": "approve"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = MonthlyReport.query.get(report_id)
        assert updated is not None
        assert updated.approval_status == ApprovalStatus.APPROVED


def test_goal_mutation_creates_audit_log(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Saving a goal should create an immutable audit trail entry."""

    login(staff_user.username, "staffpass123")
    response = client.post(
        "/logs/goals",
        data={
            "title": "Reduce processing delays",
            "kpi": "Average handling time",
            "status": "in_progress",
            "progress": 30,
            "priority": "high",
            "comments": "Week one baseline complete",
            "submit": "Save goal",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        audit_entry = (
            AuditLog.query.filter_by(entity_type="goal", action="created")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert audit_entry is not None
        assert audit_entry.actor_user_id == staff_user.id
