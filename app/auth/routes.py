"""
ME Statistics — Auth Routes
=============================
Login, register, logout, and pending-approval views.
"""

import bcrypt
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User, SystemConfig, AuditLog


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.post_login_redirect'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.checkpw(
            form.password.data.encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.post_login_redirect'))
        else:
            # Log failed login attempt to audit trail
            audit = AuditLog(
                actor_user_id=user.id if user else 0,
                entity_type='user',
                entity_id=user.id if user else 0,
                action='login_failed',
            )
            db.session.add(audit)
            db.session.commit()
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle self-registration."""
    # Check if self-registration is enabled
    allow_registration = SystemConfig.get('allow_self_registration', 'true')
    if allow_registration != 'true':
        flash('Self-registration is currently disabled. Please contact an administrator.', 'warning')
        return redirect(url_for('auth.login'))

    if current_user.is_authenticated:
        return redirect(url_for('auth.post_login_redirect'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Hash password with bcrypt
        password_hash = bcrypt.hashpw(
            form.password.data.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            password_hash=password_hash,
            role='user',
            is_approved=False,  # Requires admin approval
        )
        db.session.add(user)
        db.session.commit()

        # Notify admins of new registration
        from app.notifications.helpers import notify_all_admins
        notify_all_admins(
            'registration',
            f'New registration: {user.full_name} is awaiting approval.',
            link=url_for('users.manage')
        )
        db.session.commit()

        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.pending_approval_info'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/pending')
@login_required
def pending_approval():
    """Page shown to users who are logged in but not yet approved."""
    if current_user.is_approved:
        return redirect(url_for('auth.post_login_redirect'))
    return render_template('auth/pending.html')


@auth_bp.route('/pending-info')
def pending_approval_info():
    """Info page shown after registration (no login required)."""
    return render_template('auth/pending_info.html')


@auth_bp.route('/redirect')
@login_required
def post_login_redirect():
    """Smart redirect after login — routes to appropriate dashboard."""
    if not current_user.is_approved:
        return redirect(url_for('auth.pending_approval'))
    if current_user.is_admin:
        return redirect(url_for('dashboard.admin'))
    return redirect(url_for('dashboard.staff'))


@auth_bp.route('/home')
@login_required
def home():
    """Redirect to the appropriate dashboard."""
    if not current_user.is_approved:
        return redirect(url_for('auth.pending_approval'))
    if current_user.is_admin:
        return redirect(url_for('dashboard.admin'))
    return redirect(url_for('dashboard.staff'))

