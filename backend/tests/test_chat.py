from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def force_mock_provider(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.llm_provider", "mock")


def test_chat_updates_state():
    # 1. Create session
    session_res = client.post("/api/session")
    session_id = session_res.json()["session_id"]
    
    # 2. Send chat message that triggers the mock
    chat_res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "My name is Rahul Sharma"
    })
    
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["state"]["full_name"]["value"] == "Rahul Sharma"
    assert data["state"]["full_name"]["status"] == "confirmed"

def test_chat_invalid_session():
    import uuid
    chat_res = client.post("/api/chat", json={
        "session_id": str(uuid.uuid4()),
        "message": "Hello"
    })
    assert chat_res.status_code == 404
