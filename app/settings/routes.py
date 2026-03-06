"""
ME Statistics — Settings Routes
==================================
Admin-only system configuration page, audit log viewer, and backup/restore.
"""

import os
import shutil
import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.settings import settings_bp
from app.settings.forms import SystemSettingsForm
from app.models import SystemConfig, AuditLog
from app.auth.decorators import admin_required
import pytz


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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKUP & RESTORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _backup_dir():
    """Return the backups directory path, creating it if needed."""
    backup_path = os.path.join(current_app.instance_path, 'backups')
    os.makedirs(backup_path, exist_ok=True)
    return backup_path


def _db_path():
    """Return the active SQLite database file path."""
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    # Handle sqlite:///relative and sqlite:////absolute
    if uri.startswith('sqlite:///'):
        db_file = uri.replace('sqlite:///', '', 1)
        if not os.path.isabs(db_file):
            db_file = os.path.join(current_app.instance_path, db_file)
    return db_file


def _format_size(size_bytes):
    """Format bytes into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _create_backup(tag='manual'):
    """Create a backup of the database. Returns filename or None on error."""
    try:
        src = _db_path()
        if not os.path.exists(src):
            return None
        tz = pytz.timezone('Asia/Riyadh')
        timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
        filename = f"me_stats_{tag}_{timestamp}.db"
        dest = os.path.join(_backup_dir(), filename)
        shutil.copy2(src, dest)
        # Enforce retention limit
        _enforce_retention()
        return filename
    except Exception:
        return None


def _list_backups():
    """List all backups sorted newest first."""
    backup_path = _backup_dir()
    backups = []
    for f in os.listdir(backup_path):
        if f.endswith('.db') and f.startswith('me_stats_'):
            fpath = os.path.join(backup_path, f)
            stat = os.stat(fpath)
            backups.append({
                'filename': f,
                'size': stat.st_size,
                'size_human': _format_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_mtime,
                               tz=pytz.timezone('Asia/Riyadh')),
            })
    backups.sort(key=lambda b: b['created'], reverse=True)
    return backups


def _enforce_retention():
    """Delete oldest backups exceeding the retention limit."""
    retention = int(SystemConfig.get('backup_retention_count', '10'))
    backups = _list_backups()
    if len(backups) > retention:
        for old in backups[retention:]:
            try:
                os.remove(os.path.join(_backup_dir(), old['filename']))
            except OSError:
                pass


def _backup_health():
    """Return health status: 'healthy', 'warning', 'overdue'."""
    interval = int(SystemConfig.get('backup_interval_days', '7'))
    if interval == 0:
        return 'disabled'
    backups = _list_backups()
    if not backups:
        return 'overdue'
    last = backups[0]['created']
    now = datetime.now(pytz.timezone('Asia/Riyadh'))
    age_days = (now - last).total_seconds() / 86400
    if age_days <= interval:
        return 'healthy'
    elif age_days <= interval * 1.5:
        return 'warning'
    return 'overdue'


@settings_bp.route('/backups')
@login_required
@admin_required
def backups():
    """Backup management page."""
    # Auto-backup check
    interval = int(SystemConfig.get('backup_interval_days', '7'))
    auto_enabled = SystemConfig.get('backup_auto_enabled', 'false') == 'true'
    if auto_enabled and interval > 0:
        backup_list = _list_backups()
        if backup_list:
            last = backup_list[0]['created']
            now = datetime.now(pytz.timezone('Asia/Riyadh'))
            if (now - last).total_seconds() > interval * 86400:
                _create_backup(tag='auto')
        else:
            _create_backup(tag='auto')

    backup_list = _list_backups()
    total_size = sum(b['size'] for b in backup_list)

    return render_template(
        'settings/backups.html',
        backups=backup_list,
        backup_count=len(backup_list),
        total_size=_format_size(total_size),
        health=_backup_health(),
        auto_enabled=auto_enabled,
        interval_days=interval,
        retention_count=int(SystemConfig.get('backup_retention_count', '10')),
    )


@settings_bp.route('/backups/now', methods=['POST'])
@login_required
@admin_required
def backup_now():
    """Create a manual backup immediately."""
    filename = _create_backup(tag='manual')
    if filename:
        # Audit log
        audit = AuditLog(
            actor_user_id=current_user.id,
            entity_type='backup',
            entity_id=0,
            action='created',
            after_json=json.dumps({'filename': filename}),
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Backup created: {filename}', 'success')
    else:
        flash('Failed to create backup.', 'error')
    return redirect(url_for('settings.backups'))


@settings_bp.route('/backups/<filename>/delete', methods=['POST'])
@login_required
@admin_required
def backup_delete(filename):
    """Delete a specific backup file."""
    fpath = os.path.join(_backup_dir(), filename)
    if os.path.exists(fpath) and filename.startswith('me_stats_'):
        os.remove(fpath)
        audit = AuditLog(
            actor_user_id=current_user.id,
            entity_type='backup',
            entity_id=0,
            action='deleted',
            after_json=json.dumps({'filename': filename}),
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Backup deleted: {filename}', 'success')
    else:
        flash('Backup file not found.', 'error')
    return redirect(url_for('settings.backups'))


@settings_bp.route('/backups/<filename>/restore', methods=['POST'])
@login_required
@admin_required
def backup_restore(filename):
    """Restore database from a backup. Creates a pre-restore safety backup first."""
    backup_file = os.path.join(_backup_dir(), filename)
    if not os.path.exists(backup_file) or not filename.startswith('me_stats_'):
        flash('Backup file not found.', 'error')
        return redirect(url_for('settings.backups'))

    # Verify the user typed RESTORE
    confirm_text = request.form.get('confirm_text', '')
    if confirm_text != 'RESTORE':
        flash('Restore cancelled — confirmation text did not match.', 'error')
        return redirect(url_for('settings.backups'))

    try:
        # 1) Create pre-restore safety backup
        safety = _create_backup(tag='prerestore')

        # 2) Dispose all connections
        db.engine.dispose()

        # 3) Copy backup over the active database
        shutil.copy2(backup_file, _db_path())

        flash(f'Database restored from {filename}. A safety backup was created: {safety}', 'success')
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'error')

    return redirect(url_for('settings.backups'))


@settings_bp.route('/backups/config', methods=['POST'])
@login_required
@admin_required
def backup_config():
    """Save backup configuration."""
    auto_enabled = 'true' if request.form.get('auto_enabled') else 'false'
    interval = request.form.get('interval_days', '7')
    retention = request.form.get('retention_count', '10')

    SystemConfig.set('backup_auto_enabled', auto_enabled, user_id=current_user.id)
    SystemConfig.set('backup_interval_days', interval, user_id=current_user.id)
    SystemConfig.set('backup_retention_count', retention, user_id=current_user.id)

    audit = AuditLog(
        actor_user_id=current_user.id,
        entity_type='backup_config',
        entity_id=0,
        action='updated',
        after_json=json.dumps({
            'auto_enabled': auto_enabled,
            'interval_days': interval,
            'retention_count': retention,
        }),
    )
    db.session.add(audit)
    db.session.commit()

    flash('Backup configuration saved.', 'success')
    return redirect(url_for('settings.backups'))
