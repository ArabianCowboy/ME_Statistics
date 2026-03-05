"""
ME Statistics — Settings Routes
==================================
Admin-only system configuration page.
"""

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
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
