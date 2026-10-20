from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_config_dependency():
    response = client.get("/config")

    assert response.status_code == 200

    data = response.json()

    assert data["app_name"] == "AI Customer Service Python Agent"
    assert data["app_env"] == "dev"
    assert isinstance(data["debug"], bool)


def test_agent_context_dependency():
    response = client.get("/agent/context")

    assert response.status_code == 200
    assert response.json() == {
        "agent": "customer service",
        "environment": "dev",
    }