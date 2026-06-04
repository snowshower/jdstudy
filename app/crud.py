from sqlalchemy.orm import Session
from . import models, schemas, auth

def get_crew_by_nickname(db: Session, nickname: str):
    return db.query(models.Crew).filter(models.Crew.nickname == nickname).first()

def get_crews(db: Session):
    return db.query(models.Crew).all()

def create_crew(db: Session, crew: schemas.CrewCreate):
    # Use plain password or hashed? User specified "password (String, Nullable=False) # 초기값 '1234'"
    # and "현재 패스워드 검증 후 새로운 비밀번호로 crews 테이블의 password를 업데이트"
    # I will use hashing for security but the column name is 'password' as requested.
    hashed_password = auth.get_password_hash(crew.password)
    
    db_crew = models.Crew(
        nickname=crew.nickname,
        password=hashed_password,
        group_name=crew.group_name,
        survey_domains=crew.survey_domains,
        survey_companies=crew.survey_companies
    )
    db.add(db_crew)
    db.commit()
    db.refresh(db_crew)
    return db_crew

def get_crew(db: Session, crew_id: int):
    return db.query(models.Crew).filter(models.Crew.id == crew_id).first()

def delete_crew(db: Session, crew_id: int):
    db_crew = get_crew(db, crew_id)
    if db_crew:
        db.delete(db_crew)
        db.commit()
    return db_crew

def update_crew_admin(db: Session, crew_id: int, update_data: schemas.CrewUpdateAdmin):
    db_crew = get_crew(db, crew_id)
    if not db_crew: return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_crew, key, value)
            
    db.commit()
    db.refresh(db_crew)
    return db_crew

def update_crew_password(db: Session, crew_id: int, new_password: str):
    db_crew = get_crew(db, crew_id)
    if not db_crew: return None
    
    db_crew.password = auth.get_password_hash(new_password)
    db.commit()
    db.refresh(db_crew)
    return db_crew

# Insight Board
def get_insight_posts(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.InsightPost)
    if search:
        query = query.filter(
            (models.InsightPost.title.contains(search)) | 
            (models.InsightPost.content.contains(search))
        )
    return query.order_by(models.InsightPost.created_at.desc()).offset(skip).limit(limit).all()

def count_insight_posts(db: Session, search: str = None):
    query = db.query(models.InsightPost)
    if search:
        query = query.filter(
            (models.InsightPost.title.contains(search)) | 
            (models.InsightPost.content.contains(search))
        )
    return query.count()

def get_insight_post(db: Session, post_id: int):
    return db.query(models.InsightPost).filter(models.InsightPost.id == post_id).first()

def create_insight_post(db: Session, post: schemas.InsightPostCreate, author_nickname: str):
    db_post = models.InsightPost(**post.model_dump(), author_nickname=author_nickname)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_insight_post(db: Session, db_post: models.InsightPost, post_update: schemas.InsightPostUpdate):
    update_data = post_update.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_post, key, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_insight_post(db: Session, post_id: int):
    db_post = db.query(models.InsightPost).filter(models.InsightPost.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post
