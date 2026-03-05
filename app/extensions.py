"""Extension instances shared across the Flask application."""

from flask_babel import Babel
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()
bcrypt = Bcrypt()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
