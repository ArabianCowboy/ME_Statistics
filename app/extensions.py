"""
ME Statistics — Extension Instances
====================================
Centralized extension initialization to avoid circular imports.
Extensions are created here, then initialized with the app in __init__.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ── Database ──────────────────────────────────────────────────
db = SQLAlchemy()

# ── Migrations ────────────────────────────────────────────────
migrate = Migrate()

# ── Authentication ────────────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# ── CSRF Protection ──────────────────────────────────────────
csrf = CSRFProtect()
