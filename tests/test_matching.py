from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash
from app import models

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matching.db"

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
    db = TestingSessionLocal()
    # Create 11 crews for testing (8 Backend, 3 Frontend)
    for i in range(8):
        db.add(models.Crew(
            nickname=f"backend_{i}",
            hashed_password=get_password_hash("pw"),
            desired_job="백엔드",
            target_company="Naver" if i < 4 else "Kakao",
            interest_keywords="Python" if i % 2 == 0 else "Java"
        ))
    for i in range(3):
        db.add(models.Crew(
            nickname=f"frontend_{i}",
            hashed_password=get_password_hash("pw"),
            desired_job="프론트엔드"
        ))
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_matching.db"):
        try:
            os.remove("./test_matching.db")
        except PermissionError:
            pass

def test_matching_flow(client):
    # 1. Login as admin
    client.post("/admin/login", json={"nickname": "snowshower", "password": "haemoglo0130"})
    
    # 2. Check dashboard
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert len(response.json()["crews"]) == 11

    # 3. Trigger matching
    response = client.post("/admin/match")
    assert response.status_code == 200
    # 8 Backend -> 2 groups (4, 4 or 5, 3 is not allowed, logic splits 8 to 4, 4)
    # 3 Frontend -> Leftover, but since no Frontend group exists, it creates one group of 3
    # Total 3 groups expected
    assert len(response.json()["groups"]) == 3

    # 4. Check results as crew
    # Logout admin
    client.post("/logout")
    # Login as backend_0
    client.post("/login", json={"nickname": "backend_0", "password": "pw"})
    
    response = client.get("/results")
    assert response.status_code == 200
    groups = response.json()["groups"]
    assert len(groups) == 3
    # Check members are loaded
    assert len(groups[0]["members"]) > 0

def test_results_before_matching(client):
    # Login as crew
    client.post("/login", json={"nickname": "backend_0", "password": "pw"})
    
    response = client.get("/results")
    assert response.status_code == 404
    assert response.json()["detail"] == "현재 매칭 준비 중입니다."
