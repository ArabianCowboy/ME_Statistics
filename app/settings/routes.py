"""
ME Statistics — Settings Routes
==================================
Admin-only system configuration page + audit log viewer.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.settings import settings_bp
from app.settings.forms import SystemSettingsForm
from app.models import SystemConfig, AuditLog
from app.auth.decorators import admin_required


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    """System settings page — admin only."""
    # Ensure defaults exist
    SystemConfig.seed_defaults()

    form = SystemSettingsForm()

    if form.validate_on_submit():
        # Save each setting
        settings_map = {
            'department_name': form.department_name.data,
            'default_monthly_target': str(form.default_monthly_target.data),
            'fiscal_year_start': form.fiscal_year_start.data,
            'default_language': form.default_language.data,
            'allow_self_registration': 'true' if form.allow_self_registration.data else 'false',
            'leaderboard_visible': 'true' if form.leaderboard_visible.data else 'false',
        }

        for key, value in settings_map.items():
            SystemConfig.set(key, value, user_id=current_user.id)

        # Audit log
        audit = AuditLog(
            actor_user_id=current_user.id,
            entity_type='system_config',
            entity_id=0,
            action='updated',
        )
        db.session.add(audit)
        db.session.commit()

        flash('Settings saved successfully.', 'success')
        return redirect(url_for('settings.index'))

    # Populate form with current values
    form.department_name.data = SystemConfig.get('department_name', 'Medication Error')
    form.default_monthly_target.data = int(SystemConfig.get('default_monthly_target', '0'))
    form.fiscal_year_start.data = SystemConfig.get('fiscal_year_start', '1')
    form.default_language.data = SystemConfig.get('default_language', 'en')
    form.allow_self_registration.data = SystemConfig.get('allow_self_registration', 'true') == 'true'
    form.leaderboard_visible.data = SystemConfig.get('leaderboard_visible', 'true') == 'true'

    return render_template('settings/settings.html', form=form)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUDIT LOG VIEWER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIT_PER_PAGE = 25

@settings_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    """Browse audit trail with pagination and filters."""
    page = request.args.get('page', 1, type=int)
    entity_filter = request.args.get('entity', '')
    action_filter = request.args.get('action', '')

    query = AuditLog.query.options(
        joinedload(AuditLog.actor),
        joinedload(AuditLog.target),
    )

    if entity_filter:
        query = query.filter(AuditLog.entity_type == entity_filter)
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=AUDIT_PER_PAGE, error_out=False
    )

    # Distinct values for filter dropdowns
    entity_types = sorted({r[0] for r in db.session.query(AuditLog.entity_type).distinct().all()})
    actions = sorted({r[0] for r in db.session.query(AuditLog.action).distinct().all()})

    return render_template(
        'settings/audit_log.html',
        logs=pagination.items,
        pagination=pagination,
        entity_filter=entity_filter,
        action_filter=action_filter,
        entity_types=entity_types,
        actions=actions,
    )
