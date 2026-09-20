from pydantic import BaseModel
from typing import List, Optional, Any

class ProposedUpdate(BaseModel):
    field: str
    value: Any
    confidence: str
    is_correction: bool = False

class LLMResponse(BaseModel):
    proposed_updates: List[ProposedUpdate] = []
    clarification_needed: Optional[str] = None
    assistant_message: str
