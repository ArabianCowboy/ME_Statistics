"""Integration tests for Milestone 2 core workflow behavior."""

from __future__ import annotations

from flask import Flask

from app.extensions import db
from app.models import ApprovalStatus, Goal, MonthlyReport, Task, User


def test_monthly_report_uniqueness_enforced_in_crud_flow(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Submitting duplicate month/year report should keep single stored row."""

    login(staff_user.username, "staffpass123")

    response_one = client.post(
        "/logs/reports",
        data={
            "year": 2026,
            "month": "3",
            "report_count": 11,
            "notes": "Initial",
            "submit": "Save report",
        },
        follow_redirects=True,
    )
    assert response_one.status_code == 200

    response_two = client.post(
        "/logs/reports",
        data={
            "year": 2026,
            "month": "3",
            "report_count": 14,
            "notes": "Duplicate",
            "submit": "Save report",
        },
        follow_redirects=True,
    )
    assert response_two.status_code == 200

    with app.app_context():
        reports = MonthlyReport.query.filter_by(user_id=staff_user.id, year=2026, month=3).all()
        assert len(reports) == 1


def test_goals_crud_flow_for_staff(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Staff should be able to create, update, and delete goals."""

    login(staff_user.username, "staffpass123")

    create_response = client.post(
        "/logs/goals",
        data={
            "title": "Reduce duplicate entries",
            "kpi": "Duplicates per month",
            "status": "in_progress",
            "progress": 20,
            "priority": "high",
            "comments": "Baseline complete",
            "submit": "Save goal",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200

    with app.app_context():
        goal = Goal.query.filter_by(user_id=staff_user.id).first()
        assert goal is not None
        goal_id = goal.id

    update_response = client.post(
        "/logs/goals",
        data={
            "goal_id": str(goal_id),
            "title": "Reduce duplicate entries",
            "kpi": "Duplicates per month",
            "status": "in_progress",
            "progress": 55,
            "priority": "medium",
            "comments": "Improving",
            "submit": "Save goal",
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200

    with app.app_context():
        goal = Goal.query.get(goal_id)
        assert goal is not None
        assert goal.progress == 55

    delete_response = client.post(
        f"/logs/goals/{goal_id}/delete",
        follow_redirects=True,
    )
    assert delete_response.status_code == 200

    with app.app_context():
        assert Goal.query.get(goal_id) is None


def test_tasks_crud_flow_for_staff(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Staff should be able to create, update, and delete tasks."""

    login(staff_user.username, "staffpass123")

    create_response = client.post(
        "/logs/tasks",
        data={
            "description": "Audit March reports",
            "status": "not_started",
            "progress": 0,
            "priority": "medium",
            "comments": "Assigned this week",
            "submit": "Save task",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200

    with app.app_context():
        task = Task.query.filter_by(user_id=staff_user.id).first()
        assert task is not None
        task_id = task.id

    update_response = client.post(
        "/logs/tasks",
        data={
            "task_id": str(task_id),
            "description": "Audit March reports",
            "status": "in_progress",
            "progress": 45,
            "priority": "high",
            "comments": "Half done",
            "submit": "Save task",
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200

    with app.app_context():
        task = Task.query.get(task_id)
        assert task is not None
        assert task.progress == 45

    delete_response = client.post(
        f"/logs/tasks/{task_id}/delete",
        follow_redirects=True,
    )
    assert delete_response.status_code == 200

    with app.app_context():
        assert Task.query.get(task_id) is None


def test_admin_user_management_and_toggle_updates(
    app: Flask,
    client,
    login,
    admin_user: User,
) -> None:
    """Admin should create, edit, deactivate, and reactivate users."""

    login(admin_user.username, "adminpass123")

    create_response = client.post(
        "/users",
        data={
            "username": "managed_staff",
            "email": "managed_staff@example.com",
            "full_name": "Managed Staff",
            "role": "user",
            "monthly_target": 18,
            "password": "managedpass123",
            "is_approved": "y",
            "goal_approval_required": "y",
            "report_approval_required": "y",
            "can_create_goals": "y",
            "submit": "Create user",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200

    with app.app_context():
        managed = User.query.filter_by(username="managed_staff").first()
        assert managed is not None
        managed_id = managed.id
        assert managed.report_approval_required is True

    edit_response = client.post(
        f"/users/{managed_id}/edit",
        data={
            "user_id": str(managed_id),
            "username": "managed_staff",
            "email": "managed_staff@example.com",
            "full_name": "Managed Staff Updated",
            "role": "user",
            "preferred_lang": "en",
            "monthly_target": 25,
            "is_approved": "y",
            "goal_approval_required": "y",
            "submit": "Save changes",
        },
        follow_redirects=True,
    )
    assert edit_response.status_code == 200

    with app.app_context():
        managed = User.query.get(managed_id)
        assert managed is not None
        assert managed.monthly_target == 25
        assert managed.report_approval_required is False
        assert managed.can_create_goals is False

    deactivate_response = client.post(
        f"/users/{managed_id}/deactivate",
        follow_redirects=True,
    )
    assert deactivate_response.status_code == 200

    with app.app_context():
        managed = User.query.get(managed_id)
        assert managed is not None
        assert managed.is_active is False

    reactivate_response = client.post(
        f"/users/{managed_id}/reactivate",
        follow_redirects=True,
    )
    assert reactivate_response.status_code == 200

    with app.app_context():
        managed = User.query.get(managed_id)
        assert managed is not None
        assert managed.is_active is True


def test_can_create_goals_toggle_blocks_staff_goal_creation(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Staff with goal creation disabled should not create new goals."""

    with app.app_context():
        user = User.query.get(staff_user.id)
        user.can_create_goals = False
        db.session.commit()

    login(staff_user.username, "staffpass123")
    response = client.post(
        "/logs/goals",
        data={
            "title": "Blocked goal",
            "kpi": "N/A",
            "status": "not_started",
            "progress": 0,
            "priority": "low",
            "comments": "Should not persist",
            "submit": "Save goal",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        count = Goal.query.filter_by(user_id=staff_user.id).count()
        assert count == 0


def test_goal_approval_toggle_creates_pending_goal(
    app: Flask,
    client,
    login,
    staff_user: User,
) -> None:
    """Goal approval toggle should mark new staff goals as pending."""

    with app.app_context():
        user = User.query.get(staff_user.id)
        user.goal_approval_required = True
        db.session.commit()

    login(staff_user.username, "staffpass123")
    response = client.post(
        "/logs/goals",
        data={
            "title": "Pending goal",
            "kpi": "KPI",
            "status": "not_started",
            "progress": 0,
            "priority": "medium",
            "comments": "Pending check",
            "submit": "Save goal",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        goal = Goal.query.filter_by(user_id=staff_user.id).first()
        assert goal is not None
        assert goal.approval_status == ApprovalStatus.PENDING
