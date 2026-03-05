"""Service layer for dashboard metrics, leaderboard, and approval queue."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Dict, List, Sequence

from sqlalchemy import and_

from app.models import ApprovalStatus, Goal, MonthlyReport, User, UserRole, WorkStatus


def _month_labels() -> List[str]:
    """Return short month labels in calendar order.

    Args:
        None.

    Returns:
        List[str]: Three-letter month labels from Jan to Dec.

    Side Effects:
        None.

    Raises:
        None.
    """

    return [calendar.month_abbr[index] for index in range(1, 13)]


def _reports_for_user(user_id: int, year: int) -> List[MonthlyReport]:
    """Load approved reports for one user and year.

    Args:
        user_id: User identifier.
        year: Calendar year filter.

    Returns:
        List[MonthlyReport]: Approved report rows for given year.

    Side Effects:
        Executes database query.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    return (
        MonthlyReport.query.filter(
            and_(
                MonthlyReport.user_id == user_id,
                MonthlyReport.year == year,
                MonthlyReport.approval_status == ApprovalStatus.APPROVED,
            )
        )
        .order_by(MonthlyReport.month.asc())
        .all()
    )


def _monthly_totals(reports: Sequence[MonthlyReport]) -> List[int]:
    """Build a fixed-size monthly totals array from report rows.

    Args:
        reports: Report rows to aggregate.

    Returns:
        List[int]: Report totals for months 1..12.

    Side Effects:
        None.

    Raises:
        None.
    """

    totals = [0] * 12
    for report in reports:
        month_index = report.month - 1
        if 0 <= month_index < 12:
            totals[month_index] = report.report_count
    return totals


def _encouragement_key(report_count: int, target: int) -> str:
    """Select motivational message key based on target progress.

    Args:
        report_count: Current month total reports.
        target: Current month target.

    Returns:
        str: Translation key for encouragement message.

    Side Effects:
        None.

    Raises:
        None.
    """

    if target <= 0:
        return "motivation.below_target"

    ratio = report_count / target
    if ratio >= 1:
        return "motivation.above_target"
    if ratio >= 0.8:
        return "motivation.near_target"
    return "motivation.below_target"


def staff_dashboard_payload(user: User, year: int) -> Dict[str, object]:
    """Build metric payload for staff dashboard cards and trend chart.

    Args:
        user: Staff user whose data is displayed.
        year: Selected year.

    Returns:
        Dict[str, object]: Metrics and chart-ready arrays.

    Side Effects:
        Executes report and goal database queries.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    reports = _reports_for_user(user_id=user.id, year=year)
    monthly_totals = _monthly_totals(reports)
    target_series = [user.monthly_target for _ in range(12)]

    current_month_index = datetime.utcnow().month - 1
    current_month_value = monthly_totals[current_month_index]
    current_month_target = user.monthly_target
    ytd_total = sum(monthly_totals)
    achievement_pct = 0.0
    if current_month_target > 0:
        achievement_pct = round((current_month_value / current_month_target) * 100, 1)

    goals_in_progress = Goal.query.filter(
        and_(
            Goal.user_id == user.id,
            Goal.status == WorkStatus.IN_PROGRESS,
            Goal.approval_status == ApprovalStatus.APPROVED,
        )
    ).count()

    return {
        "year": year,
        "labels": _month_labels(),
        "series": monthly_totals,
        "target_series": target_series,
        "this_month_total": current_month_value,
        "this_month_target": current_month_target,
        "achievement_pct": achievement_pct,
        "target_gap": current_month_value - current_month_target,
        "ytd_total": ytd_total,
        "goals_in_progress": goals_in_progress,
        "encouragement_key": _encouragement_key(
            report_count=current_month_value,
            target=current_month_target,
        ),
    }


def leaderboard_payload(year: int, viewer: User) -> List[Dict[str, object]]:
    """Build leaderboard data with staff anonymization rules.

    Args:
        year: Selected year.
        viewer: User requesting leaderboard data.

    Returns:
        List[Dict[str, object]]: Sorted leaderboard rows.

    Side Effects:
        Executes multiple queries for user and report aggregates.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    staff_users = (
        User.query.filter_by(role=UserRole.USER, is_active=True, is_approved=True)
        .order_by(User.full_name.asc(), User.id.asc())
        .all()
    )

    rows: List[Dict[str, object]] = []
    for user in staff_users:
        reports = _reports_for_user(user_id=user.id, year=year)
        monthly_totals = _monthly_totals(reports)
        ytd_total = sum(monthly_totals)
        months_with_data = len([value for value in monthly_totals if value > 0])
        avg_monthly = round(
            ytd_total / months_with_data,
            1,
        ) if months_with_data > 0 else 0.0

        achievement_pct = 0.0
        if user.monthly_target > 0:
            achievement_pct = round((avg_monthly / user.monthly_target) * 100, 1)

        rows.append(
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "ytd_total": ytd_total,
                "avg_monthly": avg_monthly,
                "target": user.monthly_target,
                "achievement_pct": achievement_pct,
            }
        )

    rows.sort(key=lambda item: (item["ytd_total"], item["avg_monthly"]), reverse=True)

    anonymized_index = 1
    for rank, row in enumerate(rows, start=1):
        is_current_user = int(row["user_id"]) == viewer.id
        row["rank"] = rank
        row["is_current_user"] = is_current_user

        if viewer.role == UserRole.ADMIN:
            row["display_name"] = row["full_name"]
            continue

        if is_current_user:
            row["display_name"] = "You"
        else:
            row["display_name"] = f"Staff {chr(64 + anonymized_index)}"
            anonymized_index += 1

    return rows


def comparison_payload(user_ids: Sequence[int], year: int) -> Dict[str, object]:
    """Build chart-ready series for admin user comparison chart.

    Args:
        user_ids: User IDs selected for comparison.
        year: Selected year.

    Returns:
        Dict[str, object]: Labels and datasets for chart rendering.

    Side Effects:
        Executes database lookups for selected users and reports.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    datasets: List[Dict[str, object]] = []
    for user_id in user_ids:
        user = User.query.get(user_id)
        if user is None or user.role != UserRole.USER or not user.is_active:
            continue

        reports = _reports_for_user(user_id=user.id, year=year)
        datasets.append(
            {
                "user_id": user.id,
                "name": user.full_name,
                "values": _monthly_totals(reports),
            }
        )

    return {
        "labels": _month_labels(),
        "datasets": datasets,
        "year": year,
    }


def admin_summary_payload(year: int) -> Dict[str, int]:
    """Build summary card values for admin dashboard.

    Args:
        year: Selected year.

    Returns:
        Dict[str, int]: Summary card metrics.

    Side Effects:
        Executes aggregate count queries.

    Raises:
        Any SQLAlchemy errors raised during query execution.
    """

    total_staff = User.query.filter_by(
        role=UserRole.USER,
        is_active=True,
        is_approved=True,
    ).count()

    pending_goals = Goal.query.filter_by(approval_status=ApprovalStatus.PENDING).count()
    pending_reports = MonthlyReport.query.filter_by(
        approval_status=ApprovalStatus.PENDING
    ).count()

    team_reports = MonthlyReport.query.filter(
        and_(
            MonthlyReport.year == year,
            MonthlyReport.approval_status == ApprovalStatus.APPROVED,
        )
    ).count()

    return {
        "total_staff": total_staff,
        "pending_approvals": pending_goals + pending_reports,
        "team_reports": team_reports,
    }


def pending_queue_payload(limit: int = 20) -> Dict[str, List[Dict[str, object]]]:
    """Build pending goals and reports queue for admin review.

    Args:
        limit: Maximum number of each pending type to include.

    Returns:
        Dict[str, List[Dict[str, object]]]: Pending goals and reports details.

    Side Effects:
        Executes pending item lookup queries.

    Raises:
        Any SQLAlchemy error raised during query execution.
    """

    pending_goals = (
        Goal.query.filter_by(approval_status=ApprovalStatus.PENDING)
        .order_by(Goal.created_at.desc())
        .limit(limit)
        .all()
    )
    pending_reports = (
        MonthlyReport.query.filter_by(approval_status=ApprovalStatus.PENDING)
        .order_by(MonthlyReport.created_at.desc())
        .limit(limit)
        .all()
    )

    goal_rows: List[Dict[str, object]] = []
    for goal in pending_goals:
        goal_rows.append(
            {
                "id": goal.id,
                "user_id": goal.user_id,
                "user_name": goal.owner.full_name if goal.owner is not None else "",
                "title": goal.title,
                "progress": goal.progress,
                "priority": goal.priority.value,
            }
        )

    report_rows: List[Dict[str, object]] = []
    for report in pending_reports:
        report_rows.append(
            {
                "id": report.id,
                "user_id": report.user_id,
                "user_name": report.user.full_name if report.user is not None else "",
                "year": report.year,
                "month": report.month,
                "report_count": report.report_count,
            }
        )

    return {
        "goals": goal_rows,
        "reports": report_rows,
    }
