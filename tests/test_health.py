from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_support_ask_rejects_short_question():
    # "hi" is 2 chars, below the min_length=3 constraint - should 422
    response = client.post("/api/v1/support/ask", json={"question": "hi"})
    assert response.status_code == 422


def test_content_generate_rejects_bad_content_type():
    response = client.post(
        "/api/v1/content/generate",
        json={"content_type": "not_a_type", "platform": "twitter", "topic": "launch"},
    )
    assert response.status_code == 422
