"""
Phase 3 tests — LLM integration, validation, and state management.

All tests use the deterministic MockLLMService and do NOT require
an external API key. LLM_PROVIDER is forced to 'mock' via an autouse
fixture so that a .env containing LLM_PROVIDER=gemini/openai does
not cause tests to make real API calls.
"""

from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.intake_state import IntakeState, FieldValue
from app.models.llm_contract import LLMResponse, ProposedUpdate
from app.core.validation import validate_and_apply_updates
from app.core.prompts import get_missing_fields, ALLOWED_FIELDS

client = TestClient(app)


@pytest.fixture(autouse=True)
def force_mock_provider(monkeypatch):
    """
    Override LLM_PROVIDER to 'mock' for every test in this module.
    This prevents tests from hitting real external APIs even when
    a .env file specifies a real provider.
    """
    monkeypatch.setattr("app.core.config.settings.llm_provider", "mock")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_session() -> str:
    res = client.post("/api/session")
    assert res.status_code == 200
    return res.json()["session_id"]


def _chat(session_id: str, message: str) -> dict:
    res = client.post("/api/chat", json={"session_id": session_id, "message": message})
    assert res.status_code == 200
    return res.json()


# ---------------------------------------------------------------------------
# 1. Single field extraction
# ---------------------------------------------------------------------------

class TestSingleFieldExtraction:
    def test_name_is_extracted_and_confirmed(self):
        sid = _new_session()
        data = _chat(sid, "My name is Rahul Sharma")
        assert data["state"]["full_name"]["value"] == "Rahul Sharma"
        assert data["state"]["full_name"]["status"] == "confirmed"

    def test_address_is_extracted_and_confirmed(self):
        sid = _new_session()
        data = _chat(sid, "I live in Pune")
        assert data["state"]["home_address"]["value"] == "Pune"
        assert data["state"]["home_address"]["status"] == "confirmed"

    def test_executor_name_extracted(self):
        sid = _new_session()
        data = _chat(sid, "Priya will be my executor and she is my sister")
        assert data["state"]["executor"]["name"]["value"] == "Priya"
        assert data["state"]["executor"]["relationship"]["value"] == "sister"


# ---------------------------------------------------------------------------
# 2. Multiple fields in one message
# ---------------------------------------------------------------------------

class TestMultipleFieldsInOneMessage:
    def test_name_and_address_together(self):
        sid = _new_session()
        data = _chat(sid, "My name is Rahul Sharma and I live in Pune")
        assert data["state"]["full_name"]["value"] == "Rahul Sharma"
        assert data["state"]["home_address"]["value"] == "Pune"

    def test_children_multi_field(self):
        sid = _new_session()
        # First set has_children via "have children" trigger, then names
        data = _chat(sid, "I have two children, Amit and Riya")
        assert data["state"]["has_children"]["value"] is True
        assert data["state"]["children_names"]["value"] == ["Amit", "Riya"]


# ---------------------------------------------------------------------------
# 3. Corrections
# ---------------------------------------------------------------------------

class TestCorrections:
    def test_name_correction_replaces_confirmed_value(self):
        sid = _new_session()
        _chat(sid, "My name is Rahul Sharma")
        data = _chat(sid, "Actually I meant Rahul Verma")
        assert data["state"]["full_name"]["value"] == "Rahul Verma"
        assert data["state"]["full_name"]["status"] == "confirmed"

    def test_correction_does_not_affect_unrelated_fields(self):
        sid = _new_session()
        _chat(sid, "My name is Rahul Sharma and I live in Pune")
        _chat(sid, "Actually I meant Rahul Verma")
        # Address should be unchanged
        data = _chat(sid, "Nothing more to add")
        assert data["state"]["home_address"]["value"] == "Pune"


# ---------------------------------------------------------------------------
# 4. Ambiguous input
# ---------------------------------------------------------------------------

class TestAmbiguousInput:
    def test_ambiguous_input_does_not_update_state(self):
        """
        'everything to my family' is ambiguous — specific_gifts must stay missing.
        """
        sid = _new_session()
        data = _chat(sid, "I want everything to go to my family")
        assert data["state"]["specific_gifts"]["status"] == "missing"
        assert "clarification_needed" in data

    def test_ambiguous_input_returns_clarification(self):
        sid = _new_session()
        data = _chat(sid, "I want everything to go to my family")
        assert data["clarification_needed"] is not None


# ---------------------------------------------------------------------------
# 5. Validation unit tests (direct, no HTTP layer)
# ---------------------------------------------------------------------------

class TestValidation:
    def test_unknown_field_is_rejected(self):
        state = IntakeState()
        bad_update = ProposedUpdate(field="salary", value="50000", confidence="high")
        _, rejections = validate_and_apply_updates(state, [bad_update])
        assert any("salary" in r for r in rejections)
        # State must be unchanged
        assert state.full_name.value is None

    def test_invalid_type_is_rejected(self):
        state = IntakeState()
        bad_update = ProposedUpdate(
            field="covers_worldwide_assets", value="maybe", confidence="high"
        )
        _, rejections = validate_and_apply_updates(state, [bad_update])
        assert any("covers_worldwide_assets" in r for r in rejections)
        assert state.covers_worldwide_assets.value is None

    def test_valid_update_is_accepted(self):
        state = IntakeState()
        update = ProposedUpdate(field="full_name", value="Alice", confidence="high")
        new_state, rejections = validate_and_apply_updates(state, [update])
        assert not rejections
        assert new_state.full_name.value == "Alice"
        assert new_state.full_name.status == "confirmed"

    def test_children_names_rejected_when_has_children_is_false(self):
        state = IntakeState()
        state.has_children = FieldValue(value=False, status="confirmed")
        bad = ProposedUpdate(field="children_names", value=["Sam"], confidence="high")
        _, rejections = validate_and_apply_updates(state, [bad])
        assert any("children_names" in r for r in rejections)

    def test_multiple_updates_applied_together(self):
        state = IntakeState()
        updates = [
            ProposedUpdate(field="full_name", value="Bob", confidence="high"),
            ProposedUpdate(field="home_address", value="London", confidence="high"),
        ]
        new_state, rejections = validate_and_apply_updates(state, updates)
        assert not rejections
        assert new_state.full_name.value == "Bob"
        assert new_state.home_address.value == "London"

    def test_duplicate_confirmed_value_is_silently_skipped(self):
        state = IntakeState()
        state.full_name = FieldValue(value="Alice", status="confirmed")
        same = ProposedUpdate(field="full_name", value="Alice", confidence="high")
        new_state, rejections = validate_and_apply_updates(state, [same])
        # The skip is reported as a rejection but state value is correct
        assert new_state.full_name.value == "Alice"

    def test_correction_replaces_confirmed_field(self):
        state = IntakeState()
        state.full_name = FieldValue(value="Rahul Sharma", status="confirmed")
        correction = ProposedUpdate(
            field="full_name", value="Rahul Verma",
            confidence="high", is_correction=True,
        )
        new_state, rejections = validate_and_apply_updates(state, [correction])
        assert not rejections
        assert new_state.full_name.value == "Rahul Verma"

    def test_executor_dotted_path_update(self):
        state = IntakeState()
        update = ProposedUpdate(field="executor.name", value="James", confidence="high")
        new_state, _ = validate_and_apply_updates(state, [update])
        assert new_state.executor.name.value == "James"


# ---------------------------------------------------------------------------
# 6. Preservation of existing confirmed state
# ---------------------------------------------------------------------------

class TestStatePreservation:
    def test_unrelated_fields_are_not_cleared_on_update(self):
        state = IntakeState()
        state.full_name = FieldValue(value="Alice", status="confirmed")
        state.home_address = FieldValue(value="London", status="confirmed")

        # Only update executor.name
        update = ProposedUpdate(field="executor.name", value="Bob", confidence="high")
        new_state, _ = validate_and_apply_updates(state, [update])

        assert new_state.full_name.value == "Alice"
        assert new_state.home_address.value == "London"
        assert new_state.executor.name.value == "Bob"


# ---------------------------------------------------------------------------
# 7. Missing-fields helper
# ---------------------------------------------------------------------------

class TestGetMissingFields:
    def test_all_missing_initially(self):
        state = IntakeState()
        missing = get_missing_fields(state)
        # children_names not in list because has_children is still missing
        assert "full_name" in missing
        assert "executor.name" in missing
        assert "children_names" not in missing

    def test_children_names_appears_when_has_children_confirmed_true(self):
        state = IntakeState()
        state.has_children = FieldValue(value=True, status="confirmed")
        missing = get_missing_fields(state)
        assert "children_names" in missing

    def test_confirmed_field_removed_from_missing(self):
        state = IntakeState()
        state.full_name = FieldValue(value="Alice", status="confirmed")
        missing = get_missing_fields(state)
        assert "full_name" not in missing


# ---------------------------------------------------------------------------
# 8. LLM failure / malformed response handling
# ---------------------------------------------------------------------------

class TestLLMFailureHandling:
    def test_malformed_llm_response_returns_safe_fallback(self):
        """
        When the LLM service raises ValueError (malformed JSON) on every attempt,
        the endpoint must return 200 with a user-friendly fallback message
        and must NOT mutate state.
        """
        broken_service = AsyncMock()
        broken_service.extract.side_effect = ValueError("not valid JSON")

        # Patch at the point of use — the chat route's local reference
        with patch("app.api.routes.chat.get_llm_service", return_value=broken_service):
            sid = _new_session()
            res = client.post(
                "/api/chat",
                json={"session_id": sid, "message": "My name is Rahul Sharma"},
            )

        # Should still be 200 — fallback, not a crash
        assert res.status_code == 200
        data = res.json()
        assert "rephrase" in data["assistant_message"].lower()
        # State must be unchanged
        assert data["state"]["full_name"]["status"] == "missing"

    def test_llm_api_failure_returns_502(self):
        """
        When the LLM service raises a generic exception (network failure etc.),
        the endpoint returns 502.
        """
        failing_service = AsyncMock()
        failing_service.extract.side_effect = RuntimeError("connection refused")

        with patch("app.api.routes.chat.get_llm_service", return_value=failing_service):
            sid = _new_session()
            res = client.post(
                "/api/chat",
                json={"session_id": sid, "message": "Hello"},
            )

        assert res.status_code == 502


# ---------------------------------------------------------------------------
# 9. Allowed fields allowlist
# ---------------------------------------------------------------------------

class TestAllowedFields:
    def test_all_schema_fields_in_allowlist(self):
        required = {
            "full_name", "home_address", "covers_worldwide_assets",
            "has_children", "children_names",
            "executor.name", "executor.relationship",
            "specific_gifts", "additional_wishes",
        }
        assert required.issubset(ALLOWED_FIELDS)


# ---------------------------------------------------------------------------
# 10. Mock provider (regression from Phase 2)
# ---------------------------------------------------------------------------

class TestMockProvider:
    def test_mock_provider_runs_without_api_key(self):
        sid = _new_session()
        res = client.post(
            "/api/chat",
            json={"session_id": sid, "message": "My name is Rahul Sharma"},
        )
        assert res.status_code == 200

    def test_invalid_session_still_returns_404(self):
        import uuid
        res = client.post(
            "/api/chat",
            json={"session_id": str(uuid.uuid4()), "message": "Hello"},
        )
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 11. Gemini JSON parser (unit — no live API)
# ---------------------------------------------------------------------------

class TestGeminiJsonParsing:
    """Validate the shared _parse_llm_json helper used by GeminiLLMService."""

    def test_valid_gemini_response_parses_correctly(self):
        from app.services.llm_service import _parse_llm_json

        raw = json.dumps({
            "proposed_updates": [
                {"field": "full_name", "value": "Alice", "confidence": "high", "is_correction": False}
            ],
            "clarification_needed": None,
            "assistant_message": "Got it, Alice. What is your home address?",
        })
        result = _parse_llm_json(raw)
        assert result.proposed_updates[0].value == "Alice"
        assert result.assistant_message.startswith("Got it")

    def test_malformed_json_raises_value_error(self):
        from app.services.llm_service import _parse_llm_json
        import pytest

        with pytest.raises(ValueError, match="non-JSON"):
            _parse_llm_json("Sorry, I cannot help with that.")

    def test_wrong_schema_raises_value_error(self):
        from app.services.llm_service import _parse_llm_json
        import pytest

        # Valid JSON but missing required 'assistant_message' field
        with pytest.raises(ValueError, match="schema"):
            _parse_llm_json(json.dumps({"proposed_updates": []}))

