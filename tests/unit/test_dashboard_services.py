"""Unit tests for dashboard service calculations and shaping."""

from __future__ import annotations

from flask import Flask

from app.dashboard.services import (
    comparison_payload,
    leaderboard_payload,
    staff_dashboard_payload,
)
from app.extensions import db
from app.models import ApprovalStatus, MonthlyReport, User, UserRole


def _seed_report(
    user_id: int,
    year: int,
    month: int,
    report_count: int,
    target_snapshot: int,
) -> None:
    """Insert one approved report row for test fixtures.

    Args:
        user_id: Owner identifier.
        year: Report year.
        month: Report month.
        report_count: Submitted report count.
        target_snapshot: Stored target snapshot.

    Returns:
        None.

    Side Effects:
        Adds one report row to SQLAlchemy session.

    Raises:
        None.
    """

    db.session.add(
        MonthlyReport(
            user_id=user_id,
            year=year,
            month=month,
            report_count=report_count,
            target_snapshot=target_snapshot,
            approval_status=ApprovalStatus.APPROVED,
        )
    )


def test_staff_dashboard_payload_builds_series(app: Flask) -> None:
    """Staff payload should include monthly series and expected aggregate values."""

    with app.app_context():
        user = User(
            username="metrics_staff",
            email="metrics_staff@example.com",
            full_name="Metrics Staff",
            role=UserRole.USER,
            monthly_target=10,
            is_active=True,
            is_approved=True,
        )
        user.set_password("metricspass123")
        db.session.add(user)
        db.session.commit()

        _seed_report(user.id, 2026, 1, 8, 10)
        _seed_report(user.id, 2026, 2, 12, 10)
        db.session.commit()

        payload = staff_dashboard_payload(user=user, year=2026)

        assert payload["series"][0] == 8
        assert payload["series"][1] == 12
        assert payload["ytd_total"] == 20
        assert len(payload["labels"]) == 12


def test_leaderboard_is_anonymized_for_staff_viewers(app: Flask) -> None:
    """Staff viewers should see anonymous names except for own row."""

    with app.app_context():
        viewer = User(
            username="viewer",
            email="viewer@example.com",
            full_name="Viewer Staff",
            role=UserRole.USER,
            monthly_target=10,
            is_active=True,
            is_approved=True,
        )
        viewer.set_password("viewerpass123")

        peer = User(
            username="peer",
            email="peer@example.com",
            full_name="Peer Staff",
            role=UserRole.USER,
            monthly_target=10,
            is_active=True,
            is_approved=True,
        )
        peer.set_password("peerpass123")
        db.session.add_all([viewer, peer])
        db.session.commit()

        _seed_report(viewer.id, 2026, 1, 7, 10)
        _seed_report(peer.id, 2026, 1, 9, 10)
        db.session.commit()

        rows = leaderboard_payload(year=2026, viewer=viewer)
        assert len(rows) == 2

        own_rows = [row for row in rows if row["user_id"] == viewer.id]
        peer_rows = [row for row in rows if row["user_id"] == peer.id]
        assert own_rows[0]["display_name"] == "You"
        assert str(peer_rows[0]["display_name"]).startswith("Staff")


def test_comparison_payload_contains_selected_users_only(app: Flask) -> None:
    """Comparison payload should include only explicitly selected staff IDs."""

    with app.app_context():
        first = User(
            username="first",
            email="first@example.com",
            full_name="First Staff",
            role=UserRole.USER,
            monthly_target=12,
            is_active=True,
            is_approved=True,
        )
        first.set_password("firstpass123")

        second = User(
            username="second",
            email="second@example.com",
            full_name="Second Staff",
            role=UserRole.USER,
            monthly_target=12,
            is_active=True,
            is_approved=True,
        )
        second.set_password("secondpass123")
        db.session.add_all([first, second])
        db.session.commit()

        _seed_report(first.id, 2026, 1, 5, 12)
        _seed_report(second.id, 2026, 1, 11, 12)
        db.session.commit()

        payload = comparison_payload(user_ids=[second.id], year=2026)

        assert payload["labels"][0] == "Jan"
        assert len(payload["datasets"]) == 1
        assert payload["datasets"][0]["name"] == "Second Staff"
