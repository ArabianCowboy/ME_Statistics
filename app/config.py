"""Configuration objects used by the Flask application."""

from __future__ import annotations

import os
from typing import Dict, Type


def _as_bool(raw_value: str, default: bool = False) -> bool:
    """Convert environment text into a boolean value.

    Args:
        raw_value: Raw string value read from environment variables.
        default: Value to return when parsing fails.

    Returns:
        bool: Parsed boolean value.

    Side Effects:
        None.

    Raises:
        None.
    """

    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class Config:
    """Default application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///me_statistics.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE", "false"))
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE", "false"))

    BABEL_DEFAULT_LOCALE = os.getenv("DEFAULT_LANGUAGE", "en")
    BABEL_DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Asia/Riyadh")

    ALLOW_SELF_REGISTRATION = _as_bool(
        os.getenv("ALLOW_SELF_REGISTRATION", "true"),
        default=True,
    )


class TestConfig(Config):
    """Test-specific configuration values."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


CONFIG_BY_NAME: Dict[str, Type[Config]] = {
    "default": Config,
    "testing": TestConfig,
}


def get_config() -> Type[Config]:
    """Return the selected configuration class.

    Args:
        None.

    Returns:
        Type[Config]: Configuration class selected by `FLASK_ENV`.

    Side Effects:
        Reads environment variables.

    Raises:
        None.
    """

    profile = os.getenv("FLASK_ENV", "default").strip().lower()
    return CONFIG_BY_NAME.get(profile, Config)
