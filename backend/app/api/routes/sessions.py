from fastapi import APIRouter
from ...services.session_service import session_service
from ...models.session import Session

router = APIRouter()

@router.post("/session", response_model=Session)
def create_session():
    return session_service.create_session()
