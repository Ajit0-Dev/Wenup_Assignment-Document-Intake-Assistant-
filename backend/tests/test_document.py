import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.session_service import session_service
from app.models.intake_state import IntakeState, FieldValue

client = TestClient(app)

def test_document_endpoint_returns_404_for_invalid_session():
    res = client.get(f"/api/document/{uuid.uuid4()}")
    assert res.status_code == 404

def test_document_endpoint_returns_html_preview():
    # 1. Create a session
    res = client.post("/api/session")
    session_id = res.json()["session_id"]
    
    # 2. Modify its state directly for the test
    session = session_service.get_session(uuid.UUID(session_id))
    session.intake_state.full_name = FieldValue(value="Rahul Sharma", status="confirmed")
    session.intake_state.has_children = FieldValue(value=True, status="confirmed")
    session.intake_state.children_names = FieldValue(value=["Amit", "Riya"], status="confirmed")
    
    # 3. Fetch the document
    doc_res = client.get(f"/api/document/{session_id}")
    assert doc_res.status_code == 200
    
    html = doc_res.json()["html_content"]
    assert "Rahul Sharma" in html
    assert "Amit, Riya" in html
    assert "[Address]" in html  # Unconfirmed field placeholder
