from fastapi.testclient import TestClient
from app.main import app
from app.services.session_service import session_service

client = TestClient(app)

def test_create_session():
    response = client.post("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "intake_state" in data
    
    # Check that it's in the store
    import uuid
    session = session_service.get_session(uuid.UUID(data["session_id"]))
    assert session is not None

def test_unique_session_ids():
    res1 = client.post("/api/session").json()
    res2 = client.post("/api/session").json()
    assert res1["session_id"] != res2["session_id"]

def test_invalid_session_retrieval():
    import uuid
    session = session_service.get_session(uuid.uuid4())
    assert session is None

