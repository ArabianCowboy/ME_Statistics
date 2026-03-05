"""
ME Statistics — Dashboard Routes & APIs
==========================================
Staff dashboard, admin dashboard, approval queue actions,
and JSON APIs for Chart.js.
"""

import json
import string
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.dashboard import dashboard_bp
from app.models import User, MonthlyReport, Goal, Task, AuditLog
from app.auth.decorators import admin_required, active_required
from app.notifications.helpers import create_notification


def _current_year():
    """Return the current year (Asia/Riyadh)."""
    return datetime.now().year


def _encouraging_message(achievement_pct):
    """Pick an encouraging message based on achievement percentage."""
    if achievement_pct is None:
        return {"text": "Set a target to track progress! 📊", "emoji": "📊"}
    elif achievement_pct >= 100:
        return {"text": "Outstanding work! 🌟", "emoji": "🌟"}
    elif achievement_pct >= 80:
        return {"text": "Almost there! 🎯", "emoji": "🎯"}
    elif achievement_pct >= 50:
        return {"text": "You've got this! 💪", "emoji": "💪"}
    else:
        return {"text": "Every report counts! 🚀", "emoji": "🚀"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAFF DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dashboard_bp.route('/')
@login_required
@active_required
def staff():
    """Staff dashboard: hero card, summary cards, chart, leaderboard."""
    year = request.args.get('year', _current_year(), type=int)
    now = datetime.now()
    current_month = now.month

    # ── Hero card: achievement for current month ──────────────
    current_report = MonthlyReport.query.filter_by(
        user_id=current_user.id, year=year, month=current_month,
        approval_status='approved'
    ).first()

    reports_this_month = current_report.report_count if current_report else 0
    target = current_user.monthly_target
    gap = reports_this_month - target if target > 0 else None
    achievement_pct = round((reports_this_month / target) * 100, 1) if target > 0 else None
    encourage = _encouraging_message(achievement_pct)

    # ── Summary cards ─────────────────────────────────────────
    # Reports logged this year
    ytd_total = db.session.query(
        func.coalesce(func.sum(MonthlyReport.report_count), 0)
    ).filter(
        MonthlyReport.user_id == current_user.id,
        MonthlyReport.year == year,
        MonthlyReport.approval_status == 'approved'
    ).scalar()

    # Goals in progress
    goals_in_progress = Goal.query.filter_by(
        user_id=current_user.id, status='in_progress',
        approval_status='approved'
    ).count()

    goals_total = Goal.query.filter_by(
        user_id=current_user.id, approval_status='approved'
    ).count()

    return render_template('dashboard/staff.html',
                           year=year,
                           reports_this_month=reports_this_month,
                           target=target,
                           gap=gap,
                           achievement_pct=achievement_pct,
                           encourage=encourage,
                           ytd_total=ytd_total,
                           goals_in_progress=goals_in_progress,
                           goals_total=goals_total,
                           current_month=current_month)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard: overview, approval queue, leaderboard, comparison."""
    year = request.args.get('year', _current_year(), type=int)

    # ── Summary cards ─────────────────────────────────────────
    total_staff = User.query.filter_by(is_active=True, is_approved=True).count()
    pending_registrations = User.query.filter_by(is_approved=False, is_active=True).count()

    # Pending approvals
    pending_goals = Goal.query.filter_by(approval_status='pending').all()
    pending_reports = MonthlyReport.query.filter_by(approval_status='pending').all()
    pending_count = len(pending_goals) + len(pending_reports)

    # Team YTD total
    team_ytd = db.session.query(
        func.coalesce(func.sum(MonthlyReport.report_count), 0)
    ).filter(
        MonthlyReport.year == year,
        MonthlyReport.approval_status == 'approved'
    ).scalar()

    # ── Staff list for comparison selector ────────────────────
    staff_list = User.query.filter_by(
        is_active=True, is_approved=True
    ).order_by(User.full_name).all()

    return render_template('dashboard/admin.html',
                           year=year,
                           total_staff=total_staff,
                           pending_registrations=pending_registrations,
                           pending_goals=pending_goals,
                           pending_reports=pending_reports,
                           pending_count=pending_count,
                           team_ytd=team_ytd,
                           staff_list=staff_list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPROVAL ACTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _log_audit(entity_type, entity_id, action, target_user_id=None):
    entry = AuditLog(
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
    )
    db.session.add(entry)


@dashboard_bp.route('/approve/goal/<int:goal_id>', methods=['POST'])
@login_required
@admin_required
def approve_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    goal.approval_status = 'approved'
    _log_audit('goal', goal.id, 'approved', target_user_id=goal.user_id)
    create_notification(
        goal.user_id, 'approval_result',
        f'Your goal "{goal.title[:40]}" has been approved! ✅',
        link=url_for('dashboard.staff')
    )
    db.session.commit()
    flash(f'Goal "{goal.title[:40]}" approved.', 'success')
    return redirect(url_for('dashboard.admin'))


@dashboard_bp.route('/reject/goal/<int:goal_id>', methods=['POST'])
@login_required
@admin_required
def reject_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    goal.approval_status = 'rejected'
    _log_audit('goal', goal.id, 'rejected', target_user_id=goal.user_id)
    create_notification(
        goal.user_id, 'approval_result',
        f'Your goal "{goal.title[:40]}" was not approved.',
        link=url_for('dashboard.staff')
    )
    db.session.commit()
    flash(f'Goal "{goal.title[:40]}" rejected.', 'info')
    return redirect(url_for('dashboard.admin'))


@dashboard_bp.route('/approve/report/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def approve_report(report_id):
    report = MonthlyReport.query.get_or_404(report_id)
    report.approval_status = 'approved'
    _log_audit('monthly_report', report.id, 'approved', target_user_id=report.user_id)
    create_notification(
        report.user_id, 'approval_result',
        f'Your report for {report.year}-{report.month:02d} has been approved! ✅',
        link=url_for('dashboard.staff')
    )
    db.session.commit()
    flash(f'Report {report.year}-{report.month:02d} approved.', 'success')
    return redirect(url_for('dashboard.admin'))


@dashboard_bp.route('/reject/report/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def reject_report(report_id):
    report = MonthlyReport.query.get_or_404(report_id)
    report.approval_status = 'rejected'
    _log_audit('monthly_report', report.id, 'rejected', target_user_id=report.user_id)
    create_notification(
        report.user_id, 'approval_result',
        f'Your report for {report.year}-{report.month:02d} was not approved.',
        link=url_for('dashboard.staff')
    )
    db.session.commit()
    flash(f'Report {report.year}-{report.month:02d} rejected.', 'info')
    return redirect(url_for('dashboard.admin'))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JSON APIs (for Chart.js fetch())
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MONTH_LABELS = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]


@dashboard_bp.route('/api/my-stats')
@login_required
@active_required
def api_my_stats():
    """Return the logged-in user's monthly data for the year."""
    year = request.args.get('year', _current_year(), type=int)

    reports = MonthlyReport.query.filter_by(
        user_id=current_user.id, year=year, approval_status='approved'
    ).all()

    monthly_data = [0] * 12
    for r in reports:
        monthly_data[r.month - 1] = r.report_count

    return jsonify({
        'year': year,
        'labels': MONTH_LABELS,
        'data': monthly_data,
        'target': current_user.monthly_target,
        'ytd_total': sum(monthly_data),
    })


@dashboard_bp.route('/api/leaderboard')
@login_required
@active_required
def api_leaderboard():
    """Leaderboard: anonymized for staff, full names for admin."""
    year = request.args.get('year', _current_year(), type=int)
    is_admin = current_user.is_admin

    # Get all active, approved users
    users = User.query.filter_by(is_active=True, is_approved=True).all()

    board = []
    for u in users:
        ytd = db.session.query(
            func.coalesce(func.sum(MonthlyReport.report_count), 0)
        ).filter(
            MonthlyReport.user_id == u.id,
            MonthlyReport.year == year,
            MonthlyReport.approval_status == 'approved'
        ).scalar()

        target_yearly = u.monthly_target * 12
        achievement = round((ytd / target_yearly) * 100, 1) if target_yearly > 0 else None

        board.append({
            'user_id': u.id,
            'ytd': ytd,
            'target': u.monthly_target,
            'target_yearly': target_yearly,
            'achievement': achievement,
        })

    # Sort by YTD descending
    board.sort(key=lambda x: x['ytd'], reverse=True)

    # Assign rank + name
    anon_letters = list(string.ascii_uppercase)
    for i, entry in enumerate(board):
        entry['rank'] = i + 1
        user_obj = next(u for u in users if u.id == entry['user_id'])

        if is_admin:
            entry['name'] = user_obj.full_name
        elif entry['user_id'] == current_user.id:
            entry['name'] = 'You'
            entry['is_you'] = True
        else:
            entry['name'] = f'Staff {anon_letters[i % 26]}'
            entry['is_you'] = False

        if not is_admin and entry['user_id'] != current_user.id:
            entry['is_you'] = False

        if entry['user_id'] == current_user.id and not is_admin:
            entry['is_you'] = True

    return jsonify({'year': year, 'leaderboard': board})


@dashboard_bp.route('/api/compare')
@login_required
@admin_required
def api_compare():
    """Admin: compare multiple staff members' monthly data."""
    year = request.args.get('year', _current_year(), type=int)
    user_ids_str = request.args.get('users', '')

    if not user_ids_str:
        return jsonify({'error': 'No users selected'}), 400

    try:
        user_ids = [int(x) for x in user_ids_str.split(',')]
    except ValueError:
        return jsonify({'error': 'Invalid user IDs'}), 400

    datasets = []
    # Color palette for comparison lines
    colors = [
        '#0D9488', '#F59E0B', '#3B82F6', '#EF4444', '#8B5CF6',
        '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#10B981'
    ]

    for idx, uid in enumerate(user_ids[:10]):  # max 10 users
        user = User.query.get(uid)
        if not user:
            continue

        reports = MonthlyReport.query.filter_by(
            user_id=uid, year=year, approval_status='approved'
        ).all()

        monthly_data = [0] * 12
        for r in reports:
            monthly_data[r.month - 1] = r.report_count

        datasets.append({
            'name': user.full_name,
            'user_id': uid,
            'data': monthly_data,
            'target': user.monthly_target,
            'color': colors[idx % len(colors)],
        })

    return jsonify({
        'year': year,
        'labels': MONTH_LABELS,
        'datasets': datasets,
    })
