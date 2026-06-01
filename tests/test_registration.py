from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

from app.main import app
from app.database import get_db
from app import models

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

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
    yield
    models.Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except PermissionError:
            pass

def test_register_crew_success(client):
    response = client.post(
        "/register",
        json={
            "nickname": "testcrew",
            "password": "testpassword",
            "desired_job": "백엔드",
            "target_company": "Naver",
            "interest_keywords": "Python, FastAPI"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nickname"] == "testcrew"
    assert "id" in data
    assert "password" not in data  # Ensure password is not returned

def test_register_crew_duplicate_nickname(client):
    # Register first time
    client.post(
        "/register",
        json={
            "nickname": "duplicate",
            "password": "pw1",
            "desired_job": "프론트엔드"
        }
    )
    # Try second time
    response = client.post(
        "/register",
        json={
            "nickname": "duplicate",
            "password": "pw2",
            "desired_job": "백엔드"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "이미 등록된 크루명입니다. 로그인해 주세요."
