"""
LLM provider implementations.

Architecture:
  LLMService         — Base class / interface
  MockLLMService     — deterministic, no API key (LLM_PROVIDER=mock)
  OpenAILLMService   — real provider  (LLM_PROVIDER=openai)
  GeminiLLMService   — real provider  (LLM_PROVIDER=gemini)

Free Gemini models (configure via GEMINI_MODEL in .env):
  gemini-2.0-flash-lite  — fastest, lowest latency, most generous free quota
  gemini-1.5-flash       — balanced capability, good free tier
  gemini-1.5-flash-8b    — smallest model, highest free RPM

The factory function `get_llm_service()` is the single injection point.
"""

from __future__ import annotations

import json
import logging
from typing import List

from ..models.llm_contract import LLMResponse, ProposedUpdate
from ..models.intake_state import IntakeState
from ..core.prompts import SYSTEM_PROMPT, build_user_turn, get_missing_fields
from ..core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base class (acts as the interface / protocol)
# ---------------------------------------------------------------------------

class LLMService:
    async def extract(
        self,
        conversation: list,
        state: IntakeState,
    ) -> LLMResponse:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock implementation — deterministic, covers all Phase 3 test scenarios
# ---------------------------------------------------------------------------

class MockLLMService(LLMService):
    """
    Deterministic mock. No API key required.
    Pattern-matches the last user message to produce realistic LLM responses.
    """

    async def extract(
        self,
        conversation: list,
        state: IntakeState,
    ) -> LLMResponse:
        last_msg = conversation[-1].get("content", "").lower() if conversation else ""
        missing = get_missing_fields(state)

        updates: List[ProposedUpdate] = []
        clarification: str | None = None

        # --- full_name ---
        if "rahul verma" in last_msg:
            updates.append(ProposedUpdate(
                field="full_name", value="Rahul Verma",
                confidence="high", is_correction=True,
            ))
        elif "rahul sharma" in last_msg:
            updates.append(ProposedUpdate(
                field="full_name", value="Rahul Sharma",
                confidence="high", is_correction=False,
            ))

        # --- home_address ---
        if "pune" in last_msg:
            updates.append(ProposedUpdate(
                field="home_address", value="Pune",
                confidence="high", is_correction=False,
            ))

        # --- covers_worldwide_assets ---
        if "worldwide" in last_msg and "yes" in last_msg:
            updates.append(ProposedUpdate(
                field="covers_worldwide_assets", value=True,
                confidence="high", is_correction=False,
            ))
        elif "worldwide" in last_msg and "no" in last_msg:
            updates.append(ProposedUpdate(
                field="covers_worldwide_assets", value=False,
                confidence="high", is_correction=False,
            ))

        # --- has_children / children_names ---
        if "no children" in last_msg or "don't have children" in last_msg:
            updates.append(ProposedUpdate(
                field="has_children", value=False,
                confidence="high", is_correction=False,
            ))
        elif "have children" in last_msg or "two children" in last_msg:
            updates.append(ProposedUpdate(
                field="has_children", value=True,
                confidence="high", is_correction=False,
            ))

        if "amit and riya" in last_msg:
            updates.append(ProposedUpdate(
                field="children_names", value=["Amit", "Riya"],
                confidence="high", is_correction=False,
            ))

        # --- executor ---
        if "priya" in last_msg:
            updates.append(ProposedUpdate(
                field="executor.name", value="Priya",
                confidence="high", is_correction=False,
            ))
        if "sister" in last_msg:
            updates.append(ProposedUpdate(
                field="executor.relationship", value="sister",
                confidence="high", is_correction=False,
            ))

        # --- ambiguous input --- (does NOT produce a proposed_update)
        if "everything" in last_msg and "family" in last_msg:
            clarification = (
                "Could you clarify what specific gifts or distributions "
                "you'd like to record for your family members?"
            )

        # Determine next question from remaining missing fields
        extracted_fields = {u.field for u in updates}
        remaining = [f for f in missing if f not in extracted_fields]

        if clarification:
            assistant_msg = clarification
        elif remaining:
            next_field = remaining[0].replace("_", " ").replace(".", " ")
            assistant_msg = f"Got it. Could you tell me your {next_field}?"
        else:
            assistant_msg = (
                "Thank you — I now have all the required information. "
                "Please review your details on the right."
            )

        return LLMResponse(
            proposed_updates=updates,
            clarification_needed=clarification,
            assistant_message=assistant_msg,
        )


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------

class OpenAILLMService(LLMService):
    """Real provider using OpenAI Chat Completions with JSON mode."""

    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required. Run: pip install openai"
            ) from exc

        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Add it to .env or use LLM_PROVIDER=mock."
            )
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def extract(self, conversation: list, state: IntakeState) -> LLMResponse:
        missing = get_missing_fields(state)
        last_user = next(
            (m["content"] for m in reversed(conversation) if m["role"] == "user"), ""
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in conversation[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": build_user_turn(last_user, state, missing)})

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
            )
        except Exception as exc:
            logger.error("OpenAI API call failed: %s", exc)
            raise

        return _parse_llm_json(response.choices[0].message.content or "")


# ---------------------------------------------------------------------------
# Gemini implementation — three free-tier models supported
# ---------------------------------------------------------------------------

class GeminiLLMService(LLMService):
    """
    Real provider using Google Gemini via the google-genai SDK.

    Free models (set GEMINI_MODEL in .env):
      gemini-2.0-flash-lite  — recommended default (fastest, free)
      gemini-1.5-flash       — balanced capability
      gemini-1.5-flash-8b    — highest free RPM limit

    Uses response_mime_type="application/json" to enforce structured output
    so the response can be reliably parsed into our LLMResponse schema.
    """

    def __init__(self) -> None:
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "google-genai package is required. Run: pip install google-genai"
            ) from exc

        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Add it to .env or use LLM_PROVIDER=mock."
            )

        from google import genai as _genai  # type: ignore
        self._client = _genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def extract(self, conversation: list, state: IntakeState) -> LLMResponse:
        from google.genai import types  # type: ignore

        missing = get_missing_fields(state)
        last_user = next(
            (m["content"] for m in reversed(conversation) if m["role"] == "user"), ""
        )

        # Build a single prompt string for Gemini (system + context + user turn)
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{build_user_turn(last_user, state, missing)}"
        )

        # Build contents: prior conversation turns + the enriched current turn
        contents = []
        for msg in conversation[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            ))
        # The enriched current turn replaces the raw last user message
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=full_prompt)],
        ))

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise

        raw = response.text or ""
        return _parse_llm_json(raw)


# ---------------------------------------------------------------------------
# Shared JSON parser
# ---------------------------------------------------------------------------

def _parse_llm_json(raw: str) -> LLMResponse:
    """Parse a raw LLM string into LLMResponse. Raises ValueError on failure."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON: {raw[:300]!r}") from exc

    try:
        return LLMResponse.model_validate(data)
    except Exception as exc:
        raise ValueError(f"LLM JSON did not match expected schema: {exc}") from exc


# ---------------------------------------------------------------------------
# Factory — single injection point
# ---------------------------------------------------------------------------

def get_llm_service() -> LLMService:
    """
    Return the configured LLM provider.

    Controlled by LLM_PROVIDER in .env:
      mock   — deterministic, no key needed (default, good for tests)
      gemini — Google Gemini free-tier models
      openai — OpenAI GPT models
    """
    provider = settings.llm_provider.lower()

    if provider == "mock":
        return MockLLMService()

    if provider == "gemini":
        return GeminiLLMService()

    if provider == "openai":
        return OpenAILLMService()

    raise ValueError(
        f"Unknown LLM_PROVIDER='{provider}'. "
        "Supported values: 'mock', 'gemini', 'openai'."
    )
