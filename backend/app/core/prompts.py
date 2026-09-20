"""
System prompt and prompt-building helpers.

All prompt content lives here so it is easy to iterate on in one place
without touching route handlers or the LLM service.
"""

from __future__ import annotations
from typing import List
from ..models.intake_state import IntakeState, FieldValue

# ---------------------------------------------------------------------------
# Allowed field names (mirrors IntakeState exactly)
# ---------------------------------------------------------------------------
ALLOWED_FIELDS: set[str] = {
    "full_name",
    "home_address",
    "covers_worldwide_assets",
    "has_children",
    "children_names",
    "executor.name",
    "executor.relationship",
    "specific_gifts",
    "additional_wishes",
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a compassionate document intake assistant helping a user create a
Personal Wishes Document. This is a FICTIONAL document for a technical
demonstration and is NOT legal advice.

Your job is to collect the following information through natural conversation:
  - full_name             (string)
  - home_address          (string)
  - covers_worldwide_assets (boolean: true/false)
  - has_children          (boolean: true/false)
  - children_names        (list of strings — only relevant when has_children is true)
  - executor.name         (string)
  - executor.relationship (string, e.g. "brother", "friend")
  - specific_gifts        (string — optional)
  - additional_wishes     (string — optional)

RULES YOU MUST FOLLOW:
1. NEVER invent or assume information. Only extract what the user explicitly states.
2. If information is vague or ambiguous (e.g. "Give everything to my family" or "distribute it equally"), do NOT extract it into gifts or wishes. Instead, do NOT propose updates and DO set clarification_needed asking for specific names/details.
3. Detect corrections (e.g. "actually", "sorry", "I meant") and mark is_correction=true.
4. Extract ALL fields mentioned in a single message — do not limit to one.
5. Only propose updates for the allowed fields listed above.
6. Always ask a concise follow-up for the next missing field.
7. Be warm and natural — not robotic.

OUTPUT FORMAT — you must return ONLY valid JSON matching this exact schema:
{
  "proposed_updates": [
    {
      "field": "<field_name>",
      "value": <extracted_value>,
      "confidence": "high" | "medium" | "low",
      "is_correction": true | false
    }
  ],
  "clarification_needed": "<question to ask>" | null,
  "assistant_message": "<your conversational reply to the user>"
}

Do NOT include any text outside the JSON object.
Do NOT apologise inside the JSON.
Do NOT wrap the JSON in markdown code fences.
"""


def build_user_turn(
    user_message: str,
    state: IntakeState,
    missing_fields: List[str],
) -> str:
    """
    Construct the user-role message that provides context to the LLM.
    We pass the current state snapshot and the list of still-needed fields
    so the model can ask intelligently without re-asking confirmed fields.
    """
    state_summary = _summarise_state(state)
    missing_str = ", ".join(missing_fields) if missing_fields else "none — all required fields collected"

    return (
        f"CURRENT STATE:\n{state_summary}\n\n"
        f"STILL NEEDED: {missing_str}\n\n"
        f"USER MESSAGE: {user_message}"
    )


def _summarise_state(state: IntakeState) -> str:
    """Produce a compact text representation of the current intake state."""
    lines: List[str] = []

    def _fmt(label: str, field: FieldValue) -> str:  # type: ignore[type-arg]
        if field.status == "missing":
            return f"  {label}: [missing]"
        if field.status == "unconfirmed":
            return f"  {label}: {field.value!r} [unconfirmed]"
        return f"  {label}: {field.value!r} [confirmed]"

    lines.append(_fmt("full_name", state.full_name))
    lines.append(_fmt("home_address", state.home_address))
    lines.append(_fmt("covers_worldwide_assets", state.covers_worldwide_assets))
    lines.append(_fmt("has_children", state.has_children))
    lines.append(_fmt("children_names", state.children_names))
    lines.append(_fmt("executor.name", state.executor.name))
    lines.append(_fmt("executor.relationship", state.executor.relationship))
    lines.append(_fmt("specific_gifts", state.specific_gifts))
    lines.append(_fmt("additional_wishes", state.additional_wishes))

    return "\n".join(lines)


def get_missing_fields(state: IntakeState) -> List[str]:
    """
    Return the ordered list of fields that still need to be collected.

    The ordering is the recommended conversation priority from the spec:
      name → address → assets → children → executor → gifts → wishes
    """
    missing: List[str] = []

    def _check(label: str, field: FieldValue) -> None:  # type: ignore[type-arg]
        if field.status in ("missing", "unconfirmed"):
            missing.append(label)

    _check("full_name", state.full_name)
    _check("home_address", state.home_address)
    _check("covers_worldwide_assets", state.covers_worldwide_assets)
    _check("has_children", state.has_children)

    # Only ask for children_names when we know the user has children
    if state.has_children.value is True:
        _check("children_names", state.children_names)

    _check("executor.name", state.executor.name)
    _check("executor.relationship", state.executor.relationship)
    _check("specific_gifts", state.specific_gifts)
    _check("additional_wishes", state.additional_wishes)

    return missing
