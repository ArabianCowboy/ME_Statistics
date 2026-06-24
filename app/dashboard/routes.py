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
        return {"text": "Set a target to track progress! 📊", "emoji": "📊", "key": "set_target"}
    elif achievement_pct >= 100:
        return {"text": "Outstanding work! 🌟", "emoji": "🌟", "key": "outstanding"}
    elif achievement_pct >= 80:
        return {"text": "Almost there! 🎯", "emoji": "🎯", "key": "almost"}
    elif achievement_pct >= 50:
        return {"text": "You've got this! 💪", "emoji": "💪", "key": "got_this"}
    else:
        return {"text": "Every report counts! 🚀", "emoji": "🚀", "key": "every_counts"}


def _check_achievements(user, year, current_month, achievement_pct,
                         ytd_total, goals_in_progress, goals_total):
    """Detect milestone achievements for the staff dashboard.

    Uses Flask session to avoid showing the same achievement toast
    on every page load within the same session.
    """
    from flask import session
    shown_key = f'achievements_shown_{user.id}_{year}_{current_month}'
    if session.get(shown_key):
        return []

    achievements = []

    # 1. First report ever
    total_reports = MonthlyReport.query.filter_by(user_id=user.id).count()
    if total_reports == 1:
        achievements.append("Welcome aboard! Your first report is in 🎉")

    # 2. Hit monthly target this month
    if achievement_pct is not None and achievement_pct >= 100:
        achievements.append("Target reached! Outstanding this month 🏆")

    # 3. All goals completed
    if goals_total > 0 and goals_in_progress == 0:
        completed = Goal.query.filter_by(
            user_id=user.id, approval_status='approved', status='completed'
        ).count()
        if completed == goals_total:
            achievements.append("All goals complete — what a year! 🌟")

    # 4. Six-month consecutive streak
    if current_month >= 6:
        streak_months = MonthlyReport.query.filter(
            MonthlyReport.user_id == user.id,
            MonthlyReport.year == year,
            MonthlyReport.month.in_(range(current_month - 5, current_month + 1))
        ).count()
        if streak_months == 6:
            achievements.append("6 months straight — incredible consistency! 🔥")

    if achievements:
        session[shown_key] = True

    return achievements


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

    # ── Achievement milestones ─────────────────────────────────
    achievements = _check_achievements(current_user, year, current_month,
                                        achievement_pct, ytd_total,
                                        goals_in_progress, goals_total)

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
                           current_month=current_month,
                           achievements=achievements)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard: overview, approval queue, leaderboard, comparison."""
    year = request.args.get('year', _current_year(), type=int)
    now = datetime.now()
    current_month = now.month

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

    # Reports this month (team total)
    reports_this_month = db.session.query(
        func.coalesce(func.sum(MonthlyReport.report_count), 0)
    ).filter(
        MonthlyReport.year == year,
        MonthlyReport.month == current_month,
        MonthlyReport.approval_status == 'approved'
    ).scalar()

    # Last month total (for trend arrow)
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = year if current_month > 1 else year - 1
    last_month_total = db.session.query(
        func.coalesce(func.sum(MonthlyReport.report_count), 0)
    ).filter(
        MonthlyReport.year == last_month_year,
        MonthlyReport.month == last_month,
        MonthlyReport.approval_status == 'approved'
    ).scalar()

    # Inactive this month: active+approved staff with no approved report this month
    active_ids = {u.id for u in User.query.filter_by(is_active=True, is_approved=True).with_entities(User.id).all()}
    if active_ids:
        submitted_ids = {
            r[0] for r in db.session.query(MonthlyReport.user_id).filter(
                MonthlyReport.user_id.in_(active_ids),
                MonthlyReport.year == year,
                MonthlyReport.month == current_month,
                MonthlyReport.approval_status == 'approved'
            ).distinct().all()
        }
        inactive_count = len(active_ids - submitted_ids)
    else:
        inactive_count = 0

    # ── Staff list for comparison selector ────────────────────
    staff_list = User.query.filter_by(
        is_active=True, is_approved=True
    ).order_by(User.full_name).all()

    return render_template('dashboard/admin.html',
                           year=year,
                           current_year=_current_year(),
                           total_staff=total_staff,
                           pending_registrations=pending_registrations,
                           pending_goals=pending_goals,
                           pending_reports=pending_reports,
                           pending_count=pending_count,
                           team_ytd=team_ytd,
                           reports_this_month=reports_this_month,
                           last_month_total=last_month_total,
                           inactive_count=inactive_count,
                           staff_list=staff_list)


@dashboard_bp.route('/admin/staff/<int:user_id>')
@login_required
@admin_required
def admin_staff_detail(user_id):
    """Admin drill-down: a single staff member's reports, goals, and tasks."""
    year = request.args.get('year', _current_year(), type=int)
    now = datetime.now()
    current_month = now.month

    staff = User.query.get_or_404(user_id)

    goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()

    # Current month report
    current_report = MonthlyReport.query.filter_by(
        user_id=user_id, year=year, month=current_month,
        approval_status='approved'
    ).first()
    reports_this_month = current_report.report_count if current_report else 0
    target = staff.monthly_target
    achievement_pct = round((reports_this_month / target) * 100, 1) if target > 0 else None

    # YTD total
    ytd_total = db.session.query(
        func.coalesce(func.sum(MonthlyReport.report_count), 0)
    ).filter(
        MonthlyReport.user_id == user_id,
        MonthlyReport.year == year,
        MonthlyReport.approval_status == 'approved'
    ).scalar()

    return render_template('dashboard/staff_detail.html',
                           year=year,
                           staff=staff,
                           goals=goals,
                           tasks=tasks,
                           reports_this_month=reports_this_month,
                           ytd_total=ytd_total,
                           achievement_pct=achievement_pct,
                           target=target,
                           current_month=current_month)


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
    """Return a user's monthly data for the year.
    Admin can pass ?user_id= to view any staff member; otherwise returns current_user."""
    year = request.args.get('year', _current_year(), type=int)
    user_id_param = request.args.get('user_id', type=int)

    if user_id_param is not None and current_user.is_admin:
        user_id = user_id_param
        user = User.query.get(user_id)
        target_val = user.monthly_target if user else 0
    else:
        user_id = current_user.id
        target_val = current_user.monthly_target

    reports = MonthlyReport.query.filter_by(
        user_id=user_id, year=year, approval_status='approved'
    ).all()

    monthly_data = [0] * 12
    for r in reports:
        monthly_data[r.month - 1] = r.report_count

    return jsonify({
        'year': year,
        'labels': MONTH_LABELS,
        'data': monthly_data,
        'target': target_val,
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


@dashboard_bp.route('/api/team-overview')
@login_required
@admin_required
def api_team_overview():
    """Admin: per-staff workload overview + team monthly series."""
    year = request.args.get('year', _current_year(), type=int)
    now = datetime.now()
    current_month = now.month

    users = User.query.filter_by(is_active=True, is_approved=True).order_by(User.full_name).all()

    # Batch-fetch all approved reports for the year to avoid N+1
    all_reports = MonthlyReport.query.filter(
        MonthlyReport.year == year,
        MonthlyReport.approval_status == 'approved'
    ).all()

    from collections import defaultdict
    by_user = defaultdict(list)
    for r in all_reports:
        by_user[r.user_id].append(r)

    # Team monthly series
    team_series = [0] * 12
    for uid, report_list in by_user.items():
        for r in report_list:
            team_series[r.month - 1] += r.report_count

    staff_data = []
    for u in users:
        reports = by_user.get(u.id, [])
        monthly = [0] * 12
        for r in reports:
            monthly[r.month - 1] = r.report_count

        ytd = sum(monthly)
        this_month = monthly[current_month - 1]
        target = u.monthly_target
        target_yearly = target * 12
        achievement_pct = round((ytd / target_yearly) * 100, 1) if target_yearly > 0 else None

        months_submitted = sum(1 for c in monthly if c > 0)

        # Streak: consecutive months ending at current month
        streak = 0
        for m in range(current_month - 1, -1, -1):
            if monthly[m] > 0:
                streak += 1
            else:
                break

        # Last report date
        dates = [r.updated_at or r.created_at for r in reports if r.updated_at or r.created_at]
        last_report = max(dates).strftime('%Y-%m-%d') if dates else None

        # Status
        expected_so_far = target * current_month
        if this_month == 0:
            status = 'inactive'
        elif target > 0 and ytd < 0.5 * expected_so_far:
            status = 'at_risk'
        else:
            status = 'on_track'

        staff_data.append({
            'user_id': u.id,
            'name': u.full_name,
            'target': target,
            'this_month': this_month,
            'ytd': ytd,
            'achievement_pct': achievement_pct,
            'target_yearly': target_yearly,
            'months_submitted': months_submitted,
            'streak': streak,
            'last_report': last_report,
            'status': status,
        })

    staff_data.sort(key=lambda x: x['ytd'], reverse=True)

    return jsonify({
        'year': year,
        'current_month': current_month,
        'team_series': team_series,
        'staff': staff_data,
    })
