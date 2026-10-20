from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_chat_success():
    response = client.post(
        "/chat",
        json={"message": "hello"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "hello", 
        "reply": "这是一个占位回复"
        }


def test_chat_rejects_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"