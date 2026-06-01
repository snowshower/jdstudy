from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Crew(Base):
    __tablename__ = "crews"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    desired_job = Column(String, nullable=False)
    
    # 쉼표 구분자 방식을 수용하되 Nullable 안정성 확보
    companies = Column(String, nullable=True)  
    tech_stacks = Column(String, nullable=True) 

    # 중간 테이블을 제거하고 StudyGroup과 1:N 다이렉트 관계로 맵핑
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="SET NULL"), nullable=True)
    study_group = relationship("StudyGroup", back_populates="members")

class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    common_companies = Column(String, nullable=True)
    common_keywords = Column(String, nullable=True)

    members = relationship("Crew", back_populates="study_group")

class InsightPost(Base):
    __tablename__ = "insight_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    content = Column(String, nullable=True)
    tag = Column(String, nullable=True)
    author_nickname = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())