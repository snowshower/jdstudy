import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models, crud, schemas

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matching_new.db"
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

def test_company_synonym_matching(db):
    # '우아한형제들' and '배민' should match (+100)
    c1 = crud.create_crew(db, schemas.CrewCreate(nickname="c1", password="p", desired_job="backend", target_company="우아한형제들", interest_keywords="MSA"))
    c2 = crud.create_crew(db, schemas.CrewCreate(nickname="c2", password="p", desired_job="backend", target_company="배민", interest_keywords="Redis"))
    
    score, data = crud.calculate_match_score(c1, c2)
    assert score >= 100
    assert "배민" in crud.normalize_company(c1.target_company)
    assert "배민" in crud.normalize_company(c2.target_company)

def test_keyword_scoring(db):
    # 2 keywords match = 2 * 20 = 40 points
    c1 = crud.create_crew(db, schemas.CrewCreate(nickname="c1", password="p", desired_job="backend", target_company="A", interest_keywords="MSA, Redis, Docker"))
    c2 = crud.create_crew(db, schemas.CrewCreate(nickname="c2", password="p", desired_job="backend", target_company="B", interest_keywords="MSA, Redis, Kubernetes"))
    
    score, data = crud.calculate_match_score(c1, c2)
    assert score == 40
    assert "MSA" in data["keywords"]
    assert "Redis" in data["keywords"]

def test_full_matching_flow(db):
    # Create 9 crews (all backend)
    # Group A: 4 people interested in '당근'
    for i in range(4):
        crud.create_crew(db, schemas.CrewCreate(
            nickname=f"daangn_{i}", 
            password="p", 
            desired_job="backend", 
            target_company="당근마켓", 
            interest_keywords="Python"
        ))
    
    # Group B: 4 people interested in 'Toss'
    for i in range(4):
        crud.create_crew(db, schemas.CrewCreate(
            nickname=f"toss_{i}", 
            password="p", 
            desired_job="backend", 
            target_company="토스", 
            interest_keywords="Java"
        ))
        
    # 1 Outlier
    crud.create_crew(db, schemas.CrewCreate(
        nickname="outlier", 
        password="p", 
        desired_job="backend", 
        target_company="Samsung", 
        interest_keywords="C++"
    ))
    
    groups = crud.perform_matching(db)
    
    # Should result in 2 groups
    assert len(groups) == 2
    
    # One group should have 5 members (4 + 1 outlier), the other 4
    counts = [len(g.members) for g in groups]
    assert 5 in counts
    assert 4 in counts
    
    # Check common keywords/company
    common_infos = [g.common_keywords for g in groups]
    assert any("당근" in info or "당근마켓" in info for info in common_infos)
    assert any("토스" in info for info in common_infos)

def test_clear_and_rematch(db):
    crud.create_crew(db, schemas.CrewCreate(nickname="c1", password="p", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c2", password="p", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c3", password="p", desired_job="backend", target_company="A", interest_keywords="K"))
    crud.create_crew(db, schemas.CrewCreate(nickname="c4", password="p", desired_job="backend", target_company="A", interest_keywords="K"))
    
    crud.perform_matching(db)
    assert db.query(models.StudyGroup).count() == 1
    
    # Rematch with 0 crews (though unrealistic, should clear DB)
    db.query(models.Crew).delete()
    db.commit()
    crud.perform_matching(db)
    assert db.query(models.StudyGroup).count() == 0
