from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_events_sse():
    response = client.get("/events")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )
    assert response.headers["cache-control"] == "no-cache"

    assert "data: 你好\n\n" in response.text
    assert "data: 一条\n\n" in response.text
    assert "data: 流式回复\n\n" in response.text