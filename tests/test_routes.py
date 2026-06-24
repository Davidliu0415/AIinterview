from starlette.testclient import TestClient

from app.main import app


def test_index_page_renders():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Java 面试官" in response.text


def test_history_page_renders():
    client = TestClient(app)
    response = client.get("/history")
    assert response.status_code == 200
    assert "历史记录" in response.text
