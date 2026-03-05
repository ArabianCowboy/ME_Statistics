"""Unit tests for translation and direction helper utilities."""

from __future__ import annotations

from flask import Flask

from app.i18n import get_direction, translate


def test_translate_returns_english_default(app: Flask) -> None:
    """English translation should be returned for known key in default locale."""

    with app.test_request_context("/"):
        value = translate("app.title")
        assert value == "ME Statistics"


def test_translate_supports_arabic_override(app: Flask) -> None:
    """Arabic override should load Arabic translation dictionary."""

    with app.test_request_context("/"):
        value = translate("auth.sign_in", language="ar")
        assert value == "تسجيل الدخول"


def test_get_direction_returns_expected_values() -> None:
    """Direction helper should map Arabic to RTL and English to LTR."""

    assert get_direction("ar") == "rtl"
    assert get_direction("en") == "ltr"
