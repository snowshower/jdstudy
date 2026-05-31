from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

from app.main import app
from app.database import Base, get_db

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

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    # Create a test user
    from app.auth import get_password_hash
    from app.models import Crew
    db = TestingSessionLocal()
    db.add(Crew(
        nickname="login_user",
        hashed_password=get_password_hash("password123"),
        desired_job="백엔드"
    ))
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
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
    response = client.get("/results")
    assert response.status_code == 200
    assert "매칭 결과 페이지" in response.json()["message"]

def test_logout(client):
    # Login
    client.post(
        "/login",
        json={"nickname": "login_user", "password": "password123"}
    )
    
    # Logout
    response = client.post("/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "로그아웃 성공"
    
    # Try accessing protected route again
    response = client.get("/results", follow_redirects=False)
    assert response.status_code == 303
