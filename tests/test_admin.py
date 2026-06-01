from fastapi.testclient import TestClient
from app.main import app
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_admin_login_success(client):
    response = client.post(
        "/admin/login",
        json={"nickname": "snowshower", "password": "haemoglo0130"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "관리자 로그인 성공"
    
    # Check if we can access admin dashboard
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "crews" in response.json()

def test_admin_login_failure(client):
    response = client.post(
        "/admin/login",
        json={"nickname": "snowshower", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "관리자 계정 정보가 잘못되었습니다."

def test_admin_authority_separation(client):
    # Try access without login
    response = client.get("/admin/dashboard")
    assert response.status_code == 403
