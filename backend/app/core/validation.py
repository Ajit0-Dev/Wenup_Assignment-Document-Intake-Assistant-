"""
State update and validation logic.

The core rule: the LLM proposes, the application decides.

This module is the only place that mutates IntakeState.
Nothing else should call setattr() on a state object.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from pydantic import ValidationError

from ..models.intake_state import IntakeState, FieldValue, Executor
from ..models.llm_contract import ProposedUpdate
from .prompts import ALLOWED_FIELDS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type coercion map — maps field name → expected Python type
# ---------------------------------------------------------------------------
_FIELD_TYPES: dict[str, type] = {
    "full_name": str,
    "home_address": str,
    "covers_worldwide_assets": bool,
    "has_children": bool,
    "children_names": list,
    "executor.name": str,
    "executor.relationship": str,
    "specific_gifts": str,
    "additional_wishes": str,
}


def validate_and_apply_updates(
    state: IntakeState,
    updates: List[ProposedUpdate],
) -> Tuple[IntakeState, List[str]]:
    """
    Validate each proposed update and apply safe ones to a *copy* of the state.

    Returns:
        (updated_state, list_of_rejection_reasons)

    State is never partially mutated — all validations run first, then
    accepted updates are applied atomically to a deep copy.
    """
    accepted: List[ProposedUpdate] = []
    rejections: List[str] = []

    for update in updates:
        reason = _validate_single(state, update)
        if reason:
            logger.warning("Rejecting update for '%s': %s", update.field, reason)
            rejections.append(reason)
        else:
            accepted.append(update)

    # Apply all accepted updates to a fresh copy so we never partially corrupt
    new_state = state.model_copy(deep=True)
    for update in accepted:
        _apply_update(new_state, update)

    return new_state, rejections


def _validate_single(state: IntakeState, update: ProposedUpdate) -> str | None:
    """Return a rejection reason string, or None if the update is acceptable."""

    field = update.field

    # 1. Field must be in the allowed schema
    if field not in ALLOWED_FIELDS:
        return f"Unknown field '{field}' — not part of the intake schema."

    # 2. Value must match the expected type
    expected_type = _FIELD_TYPES[field]
    value = update.value

    # Handle JSON booleans arriving as strings (e.g. "true", "false")
    if expected_type is bool and isinstance(value, str):
        lower = value.lower()
        if lower in ("true", "yes"):
            update.value = True
        elif lower in ("false", "no"):
            update.value = False
        else:
            return f"Field '{field}' expects a boolean but got '{value}'."

    # Handle list coercion — single string → list
    if expected_type is list and isinstance(value, str):
        update.value = [v.strip() for v in value.split(",") if v.strip()]

    # Final type check
    if not isinstance(update.value, expected_type):
        return (
            f"Field '{field}' expects {expected_type.__name__} "
            f"but got {type(update.value).__name__}."
        )

    # 3. Contradiction check: has_children=false but children_names provided
    if field == "children_names" and state.has_children.value is False:
        return (
            "Cannot set 'children_names' while 'has_children' is confirmed false. "
            "Resolve the contradiction first."
        )

    # 4. The application decides about corrections independently of the LLM flag.
    #    If the field is already confirmed AND the new value is IDENTICAL, skip.
    current_value = _get_current_value(state, field)
    if (
        _get_current_status(state, field) == "confirmed"
        and current_value == update.value
        and not update.is_correction
    ):
        return f"Field '{field}' already confirmed with the same value — skipping."

    return None


def _apply_update(state: IntakeState, update: ProposedUpdate) -> None:
    """Write a validated update into the state object in-place."""
    field = update.field

    if "." in field:
        parent_name, child_name = field.split(".", 1)
        parent_obj = getattr(state, parent_name)
        setattr(parent_obj, child_name, FieldValue(value=update.value, status="confirmed"))
    else:
        setattr(state, field, FieldValue(value=update.value, status="confirmed"))


def _get_current_value(state: IntakeState, field: str):
    """Get the current value of a field by dotted path."""
    if "." in field:
        parent_name, child_name = field.split(".", 1)
        return getattr(getattr(state, parent_name), child_name).value
    return getattr(state, field).value


def _get_current_status(state: IntakeState, field: str) -> str:
    """Get the current status of a field by dotted path."""
    if "." in field:
        parent_name, child_name = field.split(".", 1)
        return getattr(getattr(state, parent_name), child_name).status
    return getattr(state, field).status
