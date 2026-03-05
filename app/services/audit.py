"""Helpers for immutable audit logging of data mutations."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.inspection import inspect

from app.extensions import db
from app.models import AuditLog


def _normalize_value(value: Any) -> Any:
    """Convert non-JSON-safe values into serializable primitives.

    Args:
        value: Value extracted from a SQLAlchemy model attribute.

    Returns:
        Any: JSON-safe value representation.

    Side Effects:
        None.

    Raises:
        None.
    """

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def model_to_dict(instance: Any) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model instance to a dictionary.

    Args:
        instance: SQLAlchemy model object.

    Returns:
        Dict[str, Any]: Dictionary containing model column values.

    Side Effects:
        None.

    Raises:
        sqlalchemy.exc.NoInspectionAvailable: When model cannot be inspected.
    """

    mapper = inspect(instance.__class__)
    payload: Dict[str, Any] = {}
    for column in mapper.columns:
        payload[column.key] = _normalize_value(getattr(instance, column.key))
    return payload


def _to_json(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    """Safely dump optional dictionaries to JSON.

    Args:
        payload: Dictionary payload to serialize.

    Returns:
        Optional[str]: Serialized JSON string or `None`.

    Side Effects:
        None.

    Raises:
        TypeError: When payload contains unsupported values.
    """

    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def log_mutation(
    actor_user_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    target_user_id: Optional[int] = None,
) -> AuditLog:
    """Create and stage an immutable audit entry in the active session.

    Args:
        actor_user_id: User performing the mutation.
        entity_type: Entity class label such as `user` or `goal`.
        entity_id: Primary key of changed record.
        action: Mutation verb such as `created`, `updated`, `approved`.
        before_state: Serialized state before mutation.
        after_state: Serialized state after mutation.
        target_user_id: Optional user affected by the action.

    Returns:
        AuditLog: Newly created audit model instance.

    Side Effects:
        Adds audit row to SQLAlchemy session.

    Raises:
        Any SQLAlchemy errors when the session later commits.
    """

    entry = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=_to_json(before_state),
        after_json=_to_json(after_state),
    )
    db.session.add(entry)
    return entry
