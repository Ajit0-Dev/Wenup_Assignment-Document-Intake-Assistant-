"""
Chat route — the orchestration layer.

Flow:
  request → find session → enrich with context → call LLM abstraction
  → validate proposed updates → apply safe updates → persist → respond
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID

from ...services.session_service import session_service
from ...services.llm_service import get_llm_service
from ...core.validation import validate_and_apply_updates

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: UUID
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    # 1. Find session
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # 2. Append user message to history
    session.conversation_history.append({"role": "user", "content": request.message})

    # 3. Call LLM abstraction — this never mutates state directly
    llm_svc = get_llm_service()
    try:
        llm_response = await llm_svc.extract(
            session.conversation_history,
            session.intake_state,
        )
    except ValueError as exc:
        # Malformed LLM JSON — retry once
        logger.warning("LLM returned malformed response, retrying once: %s", exc)
        try:
            llm_response = await llm_svc.extract(
                session.conversation_history,
                session.intake_state,
            )
        except Exception:
            # Both attempts failed — return safe fallback, do not mutate state
            session.conversation_history.pop()  # remove the user message we added
            return {
                "session_id": session.session_id,
                "assistant_message": (
                    "I'm having a little trouble understanding that. "
                    "Could you rephrase your answer?"
                ),
                "state": session.intake_state,
                "warnings": ["LLM response could not be parsed."],
            }
    except Exception as exc:
        logger.error("LLM service error: %s", exc)
        raise HTTPException(status_code=502, detail="LLM service is currently unavailable.")

    # 4. Validate and apply proposed updates — never blindly trust the LLM
    new_state, rejections = validate_and_apply_updates(
        session.intake_state,
        llm_response.proposed_updates,
    )

    # 5. Persist updated state and assistant message
    session.intake_state = new_state
    session.conversation_history.append(
        {"role": "assistant", "content": llm_response.assistant_message}
    )
    session_service.update_session(session)

    response: dict = {
        "session_id": session.session_id,
        "assistant_message": llm_response.assistant_message,
        "state": session.intake_state,
    }

    # Surface non-fatal warnings to help with debugging/transparency
    if rejections:
        response["warnings"] = rejections
    if llm_response.clarification_needed:
        response["clarification_needed"] = llm_response.clarification_needed

    return response
