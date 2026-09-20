from uuid import UUID
from typing import Dict, Optional
from ..models.session import Session
from ..models.intake_state import IntakeState

class SessionService:
    def __init__(self):
        self.sessions: Dict[UUID, Session] = {}

    def create_session(self) -> Session:
        session = Session()
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[Session]:
        return self.sessions.get(session_id)

    def update_session(self, session: Session) -> None:
        self.sessions[session.session_id] = session

session_service = SessionService()
