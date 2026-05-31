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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_board.db"

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
    # Create two crews
    db.add(models.Crew(nickname="author_user", hashed_password=get_password_hash("pw"), desired_job="백엔드"))
    db.add(models.Crew(nickname="other_user", hashed_password=get_password_hash("pw"), desired_job="프론트엔드"))
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_board.db"):
        try:
            os.remove("./test_board.db")
        except PermissionError:
            pass

def test_board_lifecycle(client):
    # 1. Login as author_user
    client.post("/login", json={"nickname": "author_user", "password": "pw"})
    
    # 2. Create post
    post_data = {
        "title": "FastAPI Best Practices",
        "link": "https://fastapi.tiangolo.com/",
        "content": "Very useful documentation",
        "tag": "[기술블로그]"
    }
    response = client.post("/board", json=post_data)
    assert response.status_code == 201
    post_id = response.json()["id"]
    assert response.json()["author_nickname"] == "author_user"

    # 3. List posts
    response = client.get("/board")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "FastAPI Best Practices"

    # 4. Update post
    update_data = {"title": "FastAPI Advanced Tips"}
    response = client.put(f"/board/{post_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["title"] == "FastAPI Advanced Tips"

    # 5. Permission Check: Other user cannot update
    client.post("/logout")
    client.post("/login", json={"nickname": "other_user", "password": "pw"})
    response = client.put(f"/board/{post_id}", json={"title": "Hacked Title"})
    assert response.status_code == 403

    # 6. Admin can delete
    client.post("/logout")
    client.post("/admin/login", json={"nickname": "snowshower", "password": "haemoglo0130"})
    response = client.delete(f"/board/{post_id}")
    assert response.status_code == 204

    # 7. Check post is gone
    response = client.get("/board")
    assert response.status_code == 200
    assert len(response.json()) == 0
