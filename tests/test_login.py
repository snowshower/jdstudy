from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

from app.main import app
from app.database import get_db
from app import models

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_login.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.create_all(bind=engine)
    # Create a test user
    from app.auth import get_password_hash
    db = TestingSessionLocal()
    db.add(models.Crew(
        nickname="login_user",
        hashed_password=get_password_hash("password123"),
        desired_job="백엔드"
    ))
    db.commit()
    db.close()
    
    yield
    
    models.Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_login.db"):
        try:
            os.remove("./test_login.db")
        except PermissionError:
            pass

def test_login_success(client):
    response = client.post(
        "/login",
        json={"nickname": "login_user", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "로그인 성공"
    assert "session" in response.cookies

def test_login_failure(client):
    # Wrong password
    response = client.post(
        "/login",
        json={"nickname": "login_user", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
    # Non-existent user
    response = client.post(
        "/login",
        json={"nickname": "nobody", "password": "password123"}
    )
    assert response.status_code == 401

def test_protected_route_access(client):
    # Without login - should redirect to /login-page
    response = client.get("/results", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login-page"

    # Login
    client.post(
        "/login",
        json={"nickname": "login_user", "password": "password123"}
    )
    
    # After login
    # 매칭 결과가 없으면 404를 반환하므로, 로그인이 성공하여 권한 체크를 통과했는지 확인
    response = client.get("/results")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "groups" in response.json()

def test_logout(client):
    # Login
    client.post(
        "/login",
        json={"nickname": "login_user", "password": "password123"}
    )
    
    # Logout - 리다이렉트(303)가 발생하는지 확인
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    
    # Try accessing protected route again
    response = client.get("/results", follow_redirects=False)
    assert response.status_code == 303
