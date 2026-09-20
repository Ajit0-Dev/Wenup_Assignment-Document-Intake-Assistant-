import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def force_mock_provider(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.llm_provider", "mock")

def test_full_user_journey():
    # 1. Create session
    res = client.post("/api/session")
    assert res.status_code == 200
    session_id = res.json()["session_id"]
    
    # 2. Provide name and address
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "My name is Rahul Sharma and I live in Pune."
    })
    state = res.json()["state"]
    assert state["full_name"]["value"] == "Rahul Sharma"
    assert state["home_address"]["value"] == "Pune"
    
    # 3. Correct name
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Actually, my name is Rahul Verma"
    })
    state = res.json()["state"]
    assert state["full_name"]["value"] == "Rahul Verma"

    # 4. Provide worldwide-assets
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Yes, I have assets worldwide."
    })
    state = res.json()["state"]
    assert state["covers_worldwide_assets"]["value"] is True
    
    # 5. Provide children info
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "I have children Amit and Riya."
    })
    state = res.json()["state"]
    assert state["has_children"]["value"] is True
    assert state["children_names"]["value"] == ["Amit", "Riya"]
    
    # 6. Provide executor
    res = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "My executor is Priya, my sister."
    })
    state = res.json()["state"]
    assert state["executor"]["name"]["value"] == "Priya"
    assert state["executor"]["relationship"]["value"] == "sister"
    
    # 7. Verify document preview reflects the state, especially the correction
    doc_res = client.get(f"/api/document/{session_id}")
    assert doc_res.status_code == 200
    html = doc_res.json()["html_content"]
    
    # Check that info is there
    assert "Rahul Verma" in html
    assert "Pune" in html
    assert "Amit, Riya" in html
    assert "Priya" in html
    assert "sister" in html

