from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

from app.main import app
from app.database import get_db
from app import models

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_registration_simple.db"

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
    if os.path.exists("./test_registration_simple.db"):
        try:
            os.remove("./test_registration_simple.db")
        except PermissionError:
            pass

def test_register_crew_success(client):
    response = client.post(
        "/register",
        json={
            "nickname": "simple_crew",
            "password": "testpassword",
            "desired_job": "백엔드",
            "companies": ["카카오", "네이버"],
            "tech_stacks": ["Java", "Spring Boot", "JPA"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nickname"] == "simple_crew"
    assert len(data["companies"]) == 2
    assert "카카오" in data["companies"]
    assert len(data["tech_stacks"]) == 3
    assert "password" not in data

def test_register_crew_duplicate_nickname(client):
    # Register first time
    client.post(
        "/register",
        json={
            "nickname": "duplicate",
            "password": "pw1",
            "desired_job": "프론트엔드",
            "companies": [],
            "tech_stacks": []
        }
    )
    # Try second time
    response = client.post(
        "/register",
        json={
            "nickname": "duplicate",
            "password": "pw2",
            "desired_job": "백엔드",
            "companies": [],
            "tech_stacks": []
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "이미 등록된 크루명입니다. 로그인해 주세요."
