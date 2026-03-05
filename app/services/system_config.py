"""Service helpers for system configuration key-value settings."""

from __future__ import annotations

from typing import Dict, Optional

from app.extensions import db
from app.models import DEFAULT_SYSTEM_CONFIG, SystemConfig


def get_config_map() -> Dict[str, str]:
    """Load merged system settings with defaults and persisted overrides.

    Args:
        None.

    Returns:
        Dict[str, str]: Configuration map with guaranteed default keys.

    Side Effects:
        Reads system config rows from database.

    Raises:
        Any SQLAlchemy exception raised by query execution.
    """

    loaded = {record.key: record.value for record in SystemConfig.query.all()}
    merged = dict(DEFAULT_SYSTEM_CONFIG)
    merged.update(loaded)
    return merged


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve one system config value with fallback.

    Args:
        key: Configuration key.
        default: Fallback value when key is missing.

    Returns:
        Optional[str]: Stored value or fallback.

    Side Effects:
        Reads from database.

    Raises:
        Any SQLAlchemy exception raised by query execution.
    """

    config = SystemConfig.query.filter_by(key=key).first()
    if config is None:
        return default
    return config.value


def set_config_values(updates: Dict[str, str], actor_user_id: int) -> Dict[str, Dict[str, str]]:
    """Persist multiple system config values and return change details.

    Args:
        updates: Key-value map to persist.
        actor_user_id: Admin user ID applying the change.

    Returns:
        Dict[str, Dict[str, str]]: Changed keys with `before` and `after` values.

    Side Effects:
        Inserts/updates `SystemConfig` rows in SQLAlchemy session.

    Raises:
        Any SQLAlchemy exception raised during session operations.
    """

    changes: Dict[str, Dict[str, str]] = {}

    for key, value in updates.items():
        row = SystemConfig.query.filter_by(key=key).first()
        if row is None:
            row = SystemConfig(key=key, value=value, updated_by=actor_user_id)
            db.session.add(row)
            changes[key] = {"before": "", "after": value}
            continue

        before = row.value
        if before != value:
            row.value = value
            row.updated_by = actor_user_id
            changes[key] = {"before": before, "after": value}

    return changes
