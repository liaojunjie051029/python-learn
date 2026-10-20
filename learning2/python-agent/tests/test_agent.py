from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_agent_run():
    response = client.post(
        "/agent/run",
        json={"message": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "hello"
    assert response.json()["reply"].startswith("[dev")


def test_chat_llm_unavailable():
    response = client.post(
        "/chat",
        json={"message": "simulate_error"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "LLM service is unavailable",
    }