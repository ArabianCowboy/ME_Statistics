"""
ME Statistics — Logs Routes
==============================
CRUD routes for Monthly Reports, Goals, and Tasks.
"""

import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.logs import logs_bp
from app.logs.forms import MonthlyReportForm, GoalForm, TaskForm
from app.models import User, MonthlyReport, Goal, Task, AuditLog, SystemConfig
from app.auth.decorators import active_required, admin_required
from app.notifications.helpers import notify_all_admins, create_notification


def log_audit(action, entity_type, entity_id, target_user_id=None, before=None, after=None):
    """Log an event in the audit trail."""
    before_json = json.dumps(before) if before else None
    after_json = json.dumps(after) if after else None
    log = AuditLog(
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json
    )
    db.session.add(log)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MONTHLY REPORTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@logs_bp.route('/reports', methods=['GET'])
@login_required
@active_required
def reports():
    """List reports for the current user."""
    user_reports = MonthlyReport.query.filter_by(user_id=current_user.id).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()
    form = MonthlyReportForm()
    # Default to current year and month
    form.year.data = datetime.now().year
    form.month.data = str(datetime.now().month)
    return render_template('reports.html', reports=user_reports, form=form, target_user=current_user)


@logs_bp.route('/reports/new', methods=['POST'])
@login_required
@active_required
def reports_new():
    """Submit a new monthly report."""
    form = MonthlyReportForm()
    if form.validate_on_submit():
        # Check if already exists for this month/year
        existing = MonthlyReport.query.filter_by(
            user_id=current_user.id,
            year=form.year.data,
            month=int(form.month.data)
        ).first()
        if existing:
            flash('A report for this month already exists.', 'error')
            return redirect(url_for('logs.reports'))

        # Check approval requirements
        global_req = SystemConfig.get('report_approval_required') == 'true'
        user_req = current_user.report_approval_required
        approval_status = 'pending' if (global_req or user_req) else 'approved'

        report = MonthlyReport(
            user_id=current_user.id,
            year=form.year.data,
            month=int(form.month.data),
            report_count=form.report_count.data,
            target_snapshot=current_user.monthly_target,
            notes=form.notes.data,
            approval_status=approval_status
        )
        db.session.add(report)
        db.session.flush()  # get ID

        log_audit('created', 'monthly_report', report.id, target_user_id=current_user.id, after={
            'year': report.year,
            'month': report.month,
            'report_count': report.report_count,
            'approval_status': report.approval_status
        })

        if approval_status == 'pending':
            notify_all_admins('approval_request', f'Report pending from {current_user.full_name} for {report.year}-{report.month:02d}', link=url_for('dashboard.admin'))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the report.', 'error')
            return redirect(url_for('logs.reports'))

        if approval_status == 'pending':
            flash('Report submitted successfully and is pending approval.', 'success')
        else:
            flash('Report saved successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'error')

    return redirect(url_for('logs.reports'))


@logs_bp.route('/reports/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
@active_required
def reports_edit(report_id):
    """Edit an existing report."""
    report = MonthlyReport.query.get_or_404(report_id)
    # Check permissions
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = MonthlyReportForm(obj=report)
    if request.method == 'GET':
        form.month.data = str(report.month)

    if form.validate_on_submit():
        # Check duplicate if month/year changed
        if form.year.data != report.year or int(form.month.data) != report.month:
            existing = MonthlyReport.query.filter_by(
                user_id=report.user_id,
                year=form.year.data,
                month=int(form.month.data)
            ).first()
            if existing and existing.id != report.id:
                flash('A report for this month already exists.', 'error')
                return render_template('reports.html', form=form, editing_report=report, target_user=report.author)

        before = {
            'year': report.year,
            'month': report.month,
            'report_count': report.report_count,
            'notes': report.notes,
            'approval_status': report.approval_status
        }

        report.year = form.year.data
        report.month = int(form.month.data)
        report.report_count = form.report_count.data
        report.notes = form.notes.data

        # If user edits their own and requires approval, set back to pending
        if report.user_id == current_user.id and not current_user.is_admin:
            global_req = SystemConfig.get('report_approval_required') == 'true'
            user_req = current_user.report_approval_required
            if global_req or user_req:
                report.approval_status = 'pending'
                notify_all_admins('approval_request', f'Updated report pending from {current_user.full_name} for {report.year}-{report.month:02d}', link=url_for('dashboard.admin'))

        log_audit('updated', 'monthly_report', report.id, target_user_id=report.user_id, before=before, after={
            'year': report.year,
            'month': report.month,
            'report_count': report.report_count,
            'notes': report.notes,
            'approval_status': report.approval_status
        })

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the report.', 'error')
            if current_user.is_admin:
                return redirect(url_for('logs.admin_reports', user_id=report.user_id))
            return redirect(url_for('logs.reports'))

        flash('Report updated successfully.', 'success')
        if current_user.is_admin:
            return redirect(url_for('logs.admin_reports', user_id=report.user_id))
        return redirect(url_for('logs.reports'))

    return render_template('reports.html', form=form, editing_report=report, target_user=report.author)


@logs_bp.route('/<int:user_id>/reports', methods=['GET'])
@login_required
@admin_required
def admin_reports(user_id):
    """Admin view of a specific user's reports."""
    target_user = User.query.get_or_404(user_id)
    user_reports = MonthlyReport.query.filter_by(user_id=user_id).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()
    form = MonthlyReportForm()
    form.year.data = datetime.now().year
    form.month.data = str(datetime.now().month)
    return render_template('reports.html', reports=user_reports, form=form, target_user=target_user)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@logs_bp.route('/goals', methods=['GET'])
@login_required
@active_required
def goals():
    """List goals for the current user."""
    user_goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.created_at.desc()).all()
    form = GoalForm()
    return render_template('goals.html', goals=user_goals, form=form, target_user=current_user)


@logs_bp.route('/goals/new', methods=['POST'])
@login_required
@active_required
def goals_new():
    """Submit a new goal."""
    if not current_user.can_create_goals and not current_user.is_admin:
        abort(403)

    form = GoalForm()
    if form.validate_on_submit():
        global_req = SystemConfig.get('goal_approval_required') == 'true'
        user_req = current_user.goal_approval_required
        approval_status = 'pending' if (global_req or user_req) else 'approved'

        goal = Goal(
            title=form.title.data,
            kpi=form.kpi.data,
            priority=form.priority.data,
            status=form.status.data or 'not_started',
            progress=form.progress.data or 0,
            comments=form.comments.data,
            approval_status=approval_status,
            user_id=current_user.id,
            created_by_user_id=current_user.id
        )
        db.session.add(goal)
        db.session.flush()

        log_audit('created', 'goal', goal.id, target_user_id=current_user.id, after={
            'title': goal.title,
            'approval_status': goal.approval_status
        })

        if approval_status == 'pending':
            notify_all_admins('approval_request', f'Goal pending from {current_user.full_name}: "{goal.title[:40]}"', link=url_for('dashboard.admin'))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the goal.', 'error')
            return redirect(url_for('logs.goals'))

        if approval_status == 'pending':
            flash('Goal submitted successfully and is pending approval.', 'success')
        else:
            flash('Goal saved successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'error')

    return redirect(url_for('logs.goals'))


@logs_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
@active_required
def goals_edit(goal_id):
    """Edit an existing goal."""
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = GoalForm(obj=goal)
    if form.validate_on_submit():
        before = {
            'title': goal.title,
            'kpi': goal.kpi,
            'priority': goal.priority,
            'status': goal.status,
            'progress': goal.progress,
            'comments': goal.comments,
            'approval_status': goal.approval_status
        }

        goal.title = form.title.data
        goal.kpi = form.kpi.data
        goal.priority = form.priority.data
        goal.status = form.status.data
        goal.progress = form.progress.data
        goal.comments = form.comments.data

        if goal.user_id == current_user.id and not current_user.is_admin:
            global_req = SystemConfig.get('goal_approval_required') == 'true'
            user_req = current_user.goal_approval_required
            if global_req or user_req:
                goal.approval_status = 'pending'
                notify_all_admins('approval_request', f'Updated goal pending from {current_user.full_name}: "{goal.title[:40]}"', link=url_for('dashboard.admin'))

        log_audit('updated', 'goal', goal.id, target_user_id=goal.user_id, before=before, after={
            'title': goal.title,
            'kpi': goal.kpi,
            'priority': goal.priority,
            'status': goal.status,
            'progress': goal.progress,
            'comments': goal.comments,
            'approval_status': goal.approval_status
        })

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the goal.', 'error')
            if current_user.is_admin:
                return redirect(url_for('logs.admin_goals', user_id=goal.user_id))
            return redirect(url_for('logs.goals'))

        flash('Goal updated successfully.', 'success')
        if current_user.is_admin:
            return redirect(url_for('logs.admin_goals', user_id=goal.user_id))
        return redirect(url_for('logs.goals'))

    return render_template('goals.html', form=form, editing_goal=goal, target_user=goal.owner)


@logs_bp.route('/<int:user_id>/goals', methods=['GET'])
@login_required
@admin_required
def admin_goals(user_id):
    """Admin view of a specific user's goals."""
    target_user = User.query.get_or_404(user_id)
    user_goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
    form = GoalForm()
    return render_template('goals.html', goals=user_goals, form=form, target_user=target_user)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@logs_bp.route('/tasks', methods=['GET'])
@login_required
@active_required
def tasks():
    """List tasks for the current user."""
    user_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    form = TaskForm()
    return render_template('tasks.html', tasks=user_tasks, form=form, target_user=current_user)


@logs_bp.route('/tasks/new', methods=['POST'])
@login_required
@active_required
def tasks_new():
    """Submit a new task."""
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            description=form.description.data,
            priority=form.priority.data,
            status=form.status.data or 'not_started',
            progress=form.progress.data or 0,
            comments=form.comments.data,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.flush()

        log_audit('created', 'task', task.id, target_user_id=current_user.id, after={
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'progress': task.progress
        })

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the task.', 'error')
            return redirect(url_for('logs.tasks'))

        flash('Task saved successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'error')

    return redirect(url_for('logs.tasks'))


@logs_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@active_required
def tasks_edit(task_id):
    """Edit an existing task."""
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        before = {
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'progress': task.progress,
            'comments': task.comments
        }

        task.description = form.description.data
        task.priority = form.priority.data
        task.status = form.status.data
        task.progress = form.progress.data
        task.comments = form.comments.data

        log_audit('updated', 'task', task.id, target_user_id=task.user_id, before=before, after={
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'progress': task.progress,
            'comments': task.comments
        })

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('An error occurred while saving the task.', 'error')
            if current_user.is_admin:
                return redirect(url_for('logs.admin_tasks', user_id=task.user_id))
            return redirect(url_for('logs.tasks'))

        flash('Task updated successfully.', 'success')
        if current_user.is_admin:
            return redirect(url_for('logs.admin_tasks', user_id=task.user_id))
        return redirect(url_for('logs.tasks'))

    return render_template('tasks.html', form=form, editing_task=task, target_user=task.assignee)


@logs_bp.route('/<int:user_id>/tasks', methods=['GET'])
@login_required
@admin_required
def admin_tasks(user_id):
    """Admin view of a specific user's tasks."""
    target_user = User.query.get_or_404(user_id)
    user_tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    form = TaskForm()
    return render_template('tasks.html', tasks=user_tasks, form=form, target_user=target_user)
