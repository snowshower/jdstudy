from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class Crew(Base):
    __tablename__ = "crews"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False, default="1234")
    group_name = Column(String, nullable=False)
    survey_domains = Column(String, nullable=True)   # 관심 분야 텍스트 저장
    survey_companies = Column(String, nullable=True) # 관심 기업 텍스트 저장

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
