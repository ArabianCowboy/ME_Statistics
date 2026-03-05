"""Application factory and bootstrap wiring for ME Statistics."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

import click
from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask_login import current_user, logout_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import Config, get_config
from app.extensions import babel, bcrypt, csrf, db, login_manager, migrate
from app.i18n import SUPPORTED_LANGUAGES, get_direction, get_locale_code, translate
from app.models import LanguageCode, Notification, User, seed_default_system_config
from app.services.audit import log_mutation, model_to_dict


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Configure SQLite runtime options for each new connection.

    Args:
        dbapi_connection: Database API connection object provided by SQLAlchemy.
        connection_record: SQLAlchemy connection metadata (unused).

    Returns:
        None.

    Side Effects:
        Enables WAL journal mode and foreign key checks for SQLite connections.

    Raises:
        Any database exception raised while setting PRAGMA values.
    """

    del connection_record

    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Resolve a user ID into a `User` model instance.

    Args:
        user_id: User ID stored in the Flask-Login session.

    Returns:
        Optional[User]: Matching user row when found, otherwise `None`.

    Side Effects:
        Performs a database read through SQLAlchemy session.

    Raises:
        None.
    """

    if not user_id:
        return None

    try:
        parsed_user_id = int(user_id)
    except ValueError:
        return None

    return db.session.get(User, parsed_user_id)


def _select_locale() -> str:
    """Return the active language code for Flask-Babel.

    Args:
        None.

    Returns:
        str: Language code such as `en` or `ar`.

    Side Effects:
        Reads request-scoped user and session values.

    Raises:
        None.
    """

    return get_locale_code()


def create_app(
    config_object: Optional[Union[Type[Config], Dict[str, Any]]] = None,
) -> Flask:
    """Create and configure a Flask application instance.

    Args:
        config_object: Optional config class or mapping for runtime overrides.

    Returns:
        Flask: Fully configured Flask application object.

    Side Effects:
        Initializes Flask extensions, routes, context processors, blueprints,
        CLI commands, and error handlers.

    Raises:
        Any extension initialization error that occurs during startup.
    """

    app = Flask(__name__, instance_relative_config=True)

    if config_object is None:
        app.config.from_object(get_config())
    elif isinstance(config_object, dict):
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _register_extensions(app)
    _register_context_processors(app)
    _register_blueprints(app)
    _register_routes(app)
    _register_error_handlers(app)
    _register_cli_commands(app)

    return app


def _register_extensions(app: Flask) -> None:
    """Initialize Flask extension instances against the app.

    Args:
        app: Application instance receiving extension bindings.

    Returns:
        None.

    Side Effects:
        Binds extension state to the Flask app object.

    Raises:
        Any extension-specific initialization error.
    """

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=_select_locale)
    bcrypt.init_app(app)


def _register_context_processors(app: Flask) -> None:
    """Register template globals shared across all pages.

    Args:
        app: Application instance receiving template context processors.

    Returns:
        None.

    Side Effects:
        Adds context data to every rendered Jinja template.

    Raises:
        None.
    """

    @app.context_processor
    def inject_template_helpers() -> Dict[str, Any]:
        locale_code = get_locale_code()
        unread_count = 0
        latest_notifications = []

        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False,
            ).count()
            latest_notifications = (
                Notification.query.filter_by(user_id=current_user.id)
                .order_by(Notification.created_at.desc())
                .limit(8)
                .all()
            )

        return {
            "_t": translate,
            "current_lang": locale_code,
            "current_dir": get_direction(locale_code),
            "supported_languages": SUPPORTED_LANGUAGES,
            "notifications_unread_count": unread_count,
            "latest_notifications": latest_notifications,
        }


def _register_blueprints(app: Flask) -> None:
    """Register all blueprint modules.

    Args:
        app: Application instance receiving blueprint registrations.

    Returns:
        None.

    Side Effects:
        Adds URL rules from each blueprint to the app router.

    Raises:
        ImportError: If a blueprint module cannot be imported.
    """

    from app.auth import auth_bp
    from app.dashboard import api_bp, dashboard_bp
    from app.export import export_bp
    from app.logs import logs_bp
    from app.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(export_bp)


def _register_routes(app: Flask) -> None:
    """Register global non-blueprint routes.

    Args:
        app: Application instance receiving route definitions.

    Returns:
        None.

    Side Effects:
        Adds app-level URL rules.

    Raises:
        None.
    """

    @app.get("/")
    def index() -> ResponseReturnValue:
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if not current_user.is_active:
            logout_user()
            flash(translate("flash.account_inactive"), "error")
            return redirect(url_for("auth.login"))

        if not current_user.is_approved and not current_user.is_admin:
            return redirect(url_for("auth.pending_approval"))

        if current_user.is_admin:
            return redirect(url_for("dashboard.admin_dashboard"))

        return redirect(url_for("dashboard.staff_dashboard"))

    @app.get("/health")
    def health() -> ResponseReturnValue:
        return {"status": "ok"}, 200

    @app.post("/i18n/set/<string:lang_code>")
    def set_language(lang_code: str) -> ResponseReturnValue:
        normalized_lang = lang_code.strip().lower()
        if normalized_lang not in SUPPORTED_LANGUAGES:
            return render_template("errors/404.html"), 404

        session["lang"] = normalized_lang

        if current_user.is_authenticated:
            before_state = model_to_dict(current_user)
            current_user.preferred_lang = LanguageCode(normalized_lang)
            after_state = model_to_dict(current_user)
            try:
                log_mutation(
                    actor_user_id=current_user.id,
                    entity_type="user",
                    entity_id=current_user.id,
                    action="language_changed",
                    before_state=before_state,
                    after_state=after_state,
                    target_user_id=current_user.id,
                )
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()

        flash(translate("flash.language_changed"), "info")
        fallback = url_for("auth.login")
        if current_user.is_authenticated:
            fallback = (
                url_for("dashboard.admin_dashboard")
                if current_user.is_admin
                else url_for("dashboard.staff_dashboard")
            )

        next_url = str(request.referrer or "").strip()
        if next_url:
            return redirect(next_url)
        return redirect(fallback)


def _register_error_handlers(app: Flask) -> None:
    """Attach shared error handlers.

    Args:
        app: Application instance receiving error handlers.

    Returns:
        None.

    Side Effects:
        Registers template-based responses for HTTP errors.

    Raises:
        None.
    """

    @app.errorhandler(403)
    def forbidden(error: Exception) -> ResponseReturnValue:
        del error
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error: Exception) -> ResponseReturnValue:
        del error
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error: Exception) -> ResponseReturnValue:
        del error
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_cli_commands(app: Flask) -> None:
    """Expose convenience CLI commands for local setup.

    Args:
        app: Application instance receiving CLI command definitions.

    Returns:
        None.

    Side Effects:
        Adds custom commands to Flask CLI.

    Raises:
        None.
    """

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create all tables and seed baseline system configuration.

        Args:
            None.

        Returns:
            None.

        Side Effects:
            Creates tables in the configured database and inserts default
            `SystemConfig` rows when missing.

        Raises:
            Any SQLAlchemy exception raised while creating schema or seeding.
        """

        db.create_all()
        seed_default_system_config()
        click.echo("Database initialized.")
