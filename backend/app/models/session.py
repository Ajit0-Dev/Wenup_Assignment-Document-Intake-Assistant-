from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Dict, Any
from .intake_state import IntakeState

class Session(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    intake_state: IntakeState = Field(default_factory=IntakeState)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
