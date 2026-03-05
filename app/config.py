"""
ME Statistics — Application Configuration
==========================================
Loads settings from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with shared defaults."""

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    WTF_CSRF_ENABLED = True

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///me_statistics.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session ───────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # ── Timezone ──────────────────────────────────────────────
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Riyadh')

    # ── Babel / i18n ──────────────────────────────────────────
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Riyadh'
    LANGUAGES = ['en', 'ar']


class DevelopmentConfig(Config):
    """Development-specific settings."""
    DEBUG = True


class ProductionConfig(Config):
    """Production-specific settings."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing-specific settings."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# ── Config selector ──────────────────────────────────────────
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
