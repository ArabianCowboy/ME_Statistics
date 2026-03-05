"""Route handlers for dashboard pages, APIs, and approval actions."""

from __future__ import annotations

from datetime import datetime
from typing import List

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.auth.decorators import active_required, admin_required
from app.dashboard import api_bp, dashboard_bp
from app.dashboard.services import (
    admin_summary_payload,
    comparison_payload,
    leaderboard_payload,
    pending_queue_payload,
    staff_dashboard_payload,
)
from app.extensions import db
from app.i18n import translate
from app.models import ApprovalStatus, Goal, MonthlyReport, User, UserRole
from app.services.audit import log_mutation, model_to_dict
from app.services.notifications import create_notification


def _selected_year() -> int:
    """Parse selected year from query parameters.

    Args:
        None.

    Returns:
        int: Requested year or current year fallback.

    Side Effects:
        Reads request query parameters.

    Raises:
        None.
    """

    raw_year = str(request.args.get("year", "")).strip()
    if raw_year.isdigit():
        return int(raw_year)
    return datetime.utcnow().year


@dashboard_bp.route("/", methods=["GET"], strict_slashes=False)
@login_required
@active_required
def staff_dashboard() -> ResponseReturnValue:
    """Render staff dashboard page with server-side starter data.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered dashboard template response.

    Side Effects:
        Reads user metrics and leaderboard data from database.

    Raises:
        None.
    """

    year = _selected_year()
    metrics = staff_dashboard_payload(user=current_user, year=year)
    leaderboard_rows = leaderboard_payload(year=year, viewer=current_user)
    return render_template(
        "dashboard/staff.html",
        year=year,
        metrics=metrics,
        leaderboard=leaderboard_rows,
    )


@dashboard_bp.get("/admin")
@login_required
@active_required
@admin_required
def admin_dashboard() -> ResponseReturnValue:
    """Render admin dashboard page with summary and approval queue.

    Args:
        None.

    Returns:
        ResponseReturnValue: Rendered admin dashboard template response.

    Side Effects:
        Reads summary, leaderboard, and pending queues from database.

    Raises:
        None.
    """

    year = _selected_year()
    summary = admin_summary_payload(year=year)
    leaderboard_rows = leaderboard_payload(year=year, viewer=current_user)
    pending_queue = pending_queue_payload(limit=20)
    staff_users = (
        User.query.filter_by(is_active=True, is_approved=True)
        .filter(User.role == UserRole.USER)
        .order_by(User.full_name.asc())
        .all()
    )

    return render_template(
        "dashboard/admin.html",
        year=year,
        summary=summary,
        leaderboard=leaderboard_rows,
        pending_queue=pending_queue,
        staff_users=staff_users,
    )


@dashboard_bp.post("/approve/<string:item_type>/<int:item_id>")
@login_required
@active_required
@admin_required
def approve_item(item_type: str, item_id: int) -> ResponseReturnValue:
    """Approve or reject pending goals and reports from admin queue.

    Args:
        item_type: Entity type to mutate (`goal` or `report`).
        item_id: Entity identifier.

    Returns:
        ResponseReturnValue: Redirect to admin dashboard page.

    Side Effects:
        Updates approval statuses, writes notifications, and audit entries.

    Raises:
        werkzeug.exceptions.BadRequest: When item type/action is unsupported.
    """

    action = str(request.form.get("action", "approve")).strip().lower()
    if action not in {"approve", "reject"}:
        abort(400)

    if item_type == "goal":
        goal = Goal.query.get_or_404(item_id)
        before_state = model_to_dict(goal)
        goal.approval_status = (
            ApprovalStatus.APPROVED if action == "approve" else ApprovalStatus.REJECTED
        )

        result_message_key = (
            "notification.goal_approved" if action == "approve" else "notification.goal_rejected"
        )
        success_flash_key = (
            "flash.goal_approved" if action == "approve" else "flash.goal_rejected"
        )
        target_user_id = goal.user_id
        entity_type = "goal"
        entity_state = model_to_dict(goal)
        entity_id = goal.id

    elif item_type == "report":
        report = MonthlyReport.query.get_or_404(item_id)
        before_state = model_to_dict(report)
        report.approval_status = (
            ApprovalStatus.APPROVED if action == "approve" else ApprovalStatus.REJECTED
        )

        result_message_key = (
            "notification.report_approved"
            if action == "approve"
            else "notification.report_rejected"
        )
        success_flash_key = (
            "flash.report_approved" if action == "approve" else "flash.report_rejected"
        )
        target_user_id = report.user_id
        entity_type = "monthly_report"
        entity_state = model_to_dict(report)
        entity_id = report.id

    else:
        abort(400)

    try:
        log_mutation(
            actor_user_id=current_user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before_state,
            after_state=entity_state,
            target_user_id=target_user_id,
        )
        create_notification(
            user_id=target_user_id,
            notification_type="approval_result",
            message=translate(result_message_key),
            link=url_for("dashboard.staff_dashboard"),
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(translate("flash.approval_action_failed"), "error")
    else:
        flash(translate(success_flash_key), "success")

    return redirect(url_for("dashboard.admin_dashboard"))


@api_bp.get("/my-stats")
@login_required
@active_required
def api_my_stats() -> ResponseReturnValue:
    """Return chart and summary metrics for the current staff user.

    Args:
        None.

    Returns:
        ResponseReturnValue: JSON payload with staff metric series.

    Side Effects:
        Reads report and goal data from database.

    Raises:
        None.
    """

    year = _selected_year()
    payload = staff_dashboard_payload(user=current_user, year=year)
    return jsonify(payload)


@api_bp.get("/leaderboard")
@login_required
@active_required
def api_leaderboard() -> ResponseReturnValue:
    """Return leaderboard rows for current viewer role.

    Args:
        None.

    Returns:
        ResponseReturnValue: JSON list of leaderboard rows.

    Side Effects:
        Reads user/report data from database.

    Raises:
        None.
    """

    year = _selected_year()
    payload = leaderboard_payload(year=year, viewer=current_user)
    return jsonify(payload)


@api_bp.get("/compare")
@login_required
@active_required
@admin_required
def api_compare() -> ResponseReturnValue:
    """Return comparison datasets for selected users on admin dashboard.

    Args:
        None.

    Returns:
        ResponseReturnValue: JSON payload with labels and datasets.

    Side Effects:
        Reads user/report data from database.

    Raises:
        None.
    """

    year = _selected_year()
    users_param = str(request.args.get("users", "")).strip()
    selected_user_ids: List[int] = []
    if users_param:
        for part in users_param.split(","):
            cleaned = part.strip()
            if cleaned.isdigit():
                selected_user_ids.append(int(cleaned))

    payload = comparison_payload(user_ids=selected_user_ids, year=year)
    return jsonify(payload)
