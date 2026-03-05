"""Integration tests for dashboard API endpoints and access behavior."""

from __future__ import annotations

from app.extensions import db
from app.models import ApprovalStatus, MonthlyReport, User


def _seed_report(user_id: int, year: int, month: int, count: int, target: int) -> None:
    """Insert one approved report for API test fixtures.

    Args:
        user_id: Report owner ID.
        year: Report year.
        month: Report month.
        count: Report count.
        target: Target snapshot.

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
            report_count=count,
            target_snapshot=target,
            approval_status=ApprovalStatus.APPROVED,
        )
    )


def test_staff_leaderboard_api_returns_anonymized_names(
    app,
    client,
    login,
    staff_user: User,
) -> None:
    """Staff viewers should see anonymous names in leaderboard API output."""

    with app.app_context():
        peer = User(
            username="staff_peer",
            email="staff_peer@example.com",
            full_name="Peer Example",
            role=staff_user.role,
            monthly_target=10,
            is_active=True,
            is_approved=True,
        )
        peer.set_password("peerpass123")
        db.session.add(peer)
        db.session.commit()

        _seed_report(staff_user.id, 2026, 1, 8, 10)
        _seed_report(peer.id, 2026, 1, 11, 10)
        db.session.commit()

    login(staff_user.username, "staffpass123")
    response = client.get("/api/leaderboard?year=2026")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
    assert any(row["display_name"] == "You" for row in payload)
    assert any(str(row["display_name"]).startswith("Staff") for row in payload)


def test_admin_compare_api_returns_selected_user_datasets(
    app,
    client,
    login,
    admin_user: User,
    staff_user: User,
) -> None:
    """Admin compare endpoint should return dataset for requested user IDs."""

    with app.app_context():
        _seed_report(staff_user.id, 2026, 1, 9, 10)
        _seed_report(staff_user.id, 2026, 2, 7, 10)
        db.session.commit()

    login(admin_user.username, "adminpass123")
    response = client.get(f"/api/compare?users={staff_user.id}&year=2026")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert len(payload["datasets"]) == 1
    assert payload["datasets"][0]["user_id"] == staff_user.id
