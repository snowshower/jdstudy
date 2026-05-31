import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models, crud, schemas, database

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matching.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine)

def test_matching_algorithm(db):
    # 1. Create some crews
    crews_data = [
        # Backend Group (High similarity)
        {"nickname": "b1", "desired_job": "backend", "target_company": "당근", "interest_keywords": "Python, FastAPI"},
        {"nickname": "b2", "desired_job": "backend", "target_company": "당근마켓", "interest_keywords": "Python, SQL"},
        {"nickname": "b3", "desired_job": "backend", "target_company": "당근", "interest_keywords": "FastAPI, Docker"},
        {"nickname": "b4", "desired_job": "backend", "target_company": "당근마켓", "interest_keywords": "Python, FastAPI"},
        
        # Backend Outlier
        {"nickname": "b_out", "desired_job": "backend", "target_company": "Samsung", "interest_keywords": "Java"},
        
        # Frontend Group
        {"nickname": "f1", "desired_job": "frontend", "target_company": "Naver", "interest_keywords": "React"},
        {"nickname": "f2", "desired_job": "frontend", "target_company": "Naver", "interest_keywords": "Vue"},
        {"nickname": "f3", "desired_job": "frontend", "target_company": "Naver", "interest_keywords": "React"},
        {"nickname": "f4", "desired_job": "frontend", "target_company": "Naver", "interest_keywords": "Vue"},
    ]
    
    for c in crews_data:
        crud.create_crew(db, schemas.CrewCreate(password="pw123", **c))

    # 2. Perform matching
    groups = crud.perform_matching(db)
    
    assert len(groups) == 2
    
    # 3. Verify Backend Group
    be_groups = [g for g in groups if "backend" in g.name.lower()]
    assert len(be_groups) == 1
    be_group = be_groups[0]
    
    # Member names in BE group
    be_members = [m.crew.nickname for m in be_group.members]
    assert "b1" in be_members
    assert "b2" in be_members
    assert "b3" in be_members
    assert "b4" in be_members
    assert "b_out" in be_members  # Outlier should be distributed to this group
    assert len(be_members) == 5
    
    # Verify common_keywords (should be "당근" or "당근마켓")
    assert "당근" in be_group.common_keywords
    
    # 4. Verify Frontend Group
    fe_groups = [g for g in groups if "frontend" in g.name.lower()]
    assert len(fe_groups) == 1
    fe_group = fe_groups[0]
    fe_members = [m.crew.nickname for m in fe_group.members]
    assert len(fe_members) == 4
    assert "f1" in fe_members
    assert "Naver" in fe_group.common_keywords

def test_outlier_round_robin(db):
    # 1. Create many backend crews, 2 high-score groups and 2 outliers
    # Group 1 (4 people)
    for i in range(4):
        crud.create_crew(db, schemas.CrewCreate(
            nickname=f"g1_{i}", 
            password="pw", 
            desired_job="backend", 
            target_company="Google", 
            interest_keywords="Go"
        ))
    # Group 2 (4 people)
    for i in range(4):
        crud.create_crew(db, schemas.CrewCreate(
            nickname=f"g2_{i}", 
            password="pw", 
            desired_job="backend", 
            target_company="Meta", 
            interest_keywords="React"
        ))
    # 2 Outliers
    crud.create_crew(db, schemas.CrewCreate(nickname="out1", password="pw", desired_job="backend", target_company="X", interest_keywords="None"))
    crud.create_crew(db, schemas.CrewCreate(nickname="out2", password="pw", desired_job="backend", target_company="Y", interest_keywords="None"))

    groups = crud.perform_matching(db)
    assert len(groups) == 2
    
    # Each group should have 5 members (4 originals + 1 outlier each)
    for g in groups:
        assert len(g.members) == 5
    
    # Verify outliers are distributed
    all_members = []
    for g in groups:
        all_members.extend([m.crew.nickname for m in g.members])
    
    assert "out1" in all_members
    assert "out2" in all_members

def test_clear_and_rematch(db):
    # Initial match
    crud.create_crew(db, schemas.CrewCreate(nickname="c1", password="pw", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c2", password="pw", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c3", password="pw", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c4", password="pw", desired_job="backend", target_company="A", interest_keywords="K"))
    
    crud.perform_matching(db)
    assert db.query(models.StudyGroup).count() == 1
    
    # Add one more and rematch
    crud.create_crew(db, schemas.CrewCreate(nickname="c5", password="pw", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.perform_matching(db)
    
    # Should still be 1 group but with 5 members
    assert db.query(models.StudyGroup).count() == 1
    group = db.query(models.StudyGroup).first()
    assert len(group.members) == 5
