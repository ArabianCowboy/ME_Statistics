"""Translation helpers backed by JSON dictionaries."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from flask import current_app, has_app_context, has_request_context, session
from flask_login import current_user

from app.models import LanguageCode

SUPPORTED_LANGUAGES = (LanguageCode.EN.value, LanguageCode.AR.value)
RTL_LANGUAGES = {LanguageCode.AR.value}


def get_locale_code(explicit_language: Optional[str] = None) -> str:
    """Resolve the active language code for the current request.

    Args:
        explicit_language: Preferred language override when provided.

    Returns:
        str: Language code selected from user/session/default config.

    Side Effects:
        Reads request and application context data.

    Raises:
        None.
    """

    if explicit_language in SUPPORTED_LANGUAGES:
        return str(explicit_language)

    if has_request_context() and current_user.is_authenticated:
        preferred = getattr(current_user, "preferred_lang", None)
        preferred_value = getattr(preferred, "value", str(preferred or ""))
        if preferred_value in SUPPORTED_LANGUAGES:
            return preferred_value

    if has_request_context():
        session_lang = str(session.get("lang", "")).strip().lower()
        if session_lang in SUPPORTED_LANGUAGES:
            return session_lang

    if has_app_context():
        configured = str(current_app.config.get("BABEL_DEFAULT_LOCALE", "en"))
        configured = configured.strip().lower()
        if configured in SUPPORTED_LANGUAGES:
            return configured

    return LanguageCode.EN.value


def get_direction(language: Optional[str] = None) -> str:
    """Return text direction for a language code.

    Args:
        language: Optional language override.

    Returns:
        str: `rtl` for Arabic, otherwise `ltr`.

    Side Effects:
        None.

    Raises:
        None.
    """

    locale = get_locale_code(language)
    return "rtl" if locale in RTL_LANGUAGES else "ltr"


def _translations_path(language: str) -> Path:
    """Build absolute file path for a language dictionary.

    Args:
        language: Language code.

    Returns:
        Path: JSON file path for the selected language.

    Side Effects:
        None.

    Raises:
        RuntimeError: When called outside application context.
    """

    if not has_app_context():
        raise RuntimeError("Application context is required for translation lookups.")

    return Path(current_app.root_path) / "translations" / language / "messages.json"


@lru_cache(maxsize=8)
def _load_language_map(language: str) -> Dict[str, Any]:
    """Load and cache translation data for one language.

    Args:
        language: Language code to load.

    Returns:
        Dict[str, Any]: Translation mapping or empty dict when unavailable.

    Side Effects:
        Reads translation files from local filesystem.

    Raises:
        json.JSONDecodeError: When translation JSON is malformed.
    """

    try:
        path = _translations_path(language)
    except RuntimeError:
        return {}

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
        if isinstance(loaded, dict):
            return loaded
        return {}


def _lookup_key(mapping: Dict[str, Any], key: str) -> Optional[str]:
    """Resolve a dotted translation key from nested dictionaries.

    Args:
        mapping: Translation dictionary.
        key: Dotted key string, such as `nav.dashboard`.

    Returns:
        Optional[str]: Resolved value when found and string-based.

    Side Effects:
        None.

    Raises:
        None.
    """

    node: Any = mapping
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node.get(part)

    if isinstance(node, str):
        return node
    return None


def translate(
    key: str,
    language: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Translate a key using the active locale with English fallback.

    Args:
        key: Translation key.
        language: Optional language override.
        **kwargs: Named interpolation values used with `.format()`.

    Returns:
        str: Localized string, English fallback, or key when missing.

    Side Effects:
        None.

    Raises:
        None.
    """

    locale = get_locale_code(language)
    localized = _lookup_key(_load_language_map(locale), key)
    if localized is None:
        localized = _lookup_key(_load_language_map(LanguageCode.EN.value), key)

    if localized is None:
        return key

    if not kwargs:
        return localized

    try:
        return localized.format(**kwargs)
    except (KeyError, ValueError):
        return localized
