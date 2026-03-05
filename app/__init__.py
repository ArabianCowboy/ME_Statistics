"""
ME Statistics — Application Factory
=====================================
Creates and configures the Flask application instance.
Registers extensions, blueprints, error handlers, and the user loader.
"""

import os
from flask import Flask, render_template
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """
    Application factory — call this to create a configured Flask app.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Defaults to FLASK_ENV env var or 'development'.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

    # ── Initialize Extensions ─────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── User Loader (Flask-Login) ─────────────────────────────
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Register Blueprints ───────────────────────────────────
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.logs import logs_bp
    app.register_blueprint(logs_bp, url_prefix='/logs')

    from app.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.notifications import notifications_bp
    app.register_blueprint(notifications_bp)

    from app.export import export_bp
    app.register_blueprint(export_bp)

    # ── Root Route ────────────────────────────────────────────
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('auth.post_login_redirect'))
        return redirect(url_for('auth.login'))

    # ── Health Check ──────────────────────────────────────────
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    # ── Error Handlers ────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    return app
