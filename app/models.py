from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Crew(Base):
    __tablename__ = "crews"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    desired_job = Column(String, nullable=False)  # Backend/Frontend/Other
    target_company = Column(String)
    interest_keywords = Column(String)  # Comma separated

    # Relationship to GroupMember
    group_member_info = relationship("GroupMember", back_populates="crew", uselist=False)

class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    common_companies = Column(String)  # Top shared companies
    common_keywords = Column(String)   # Top shared keywords

    members = relationship("GroupMember", back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id"))
    crew_id = Column(Integer, ForeignKey("crews.id"))

    group = relationship("StudyGroup", back_populates="members")
    crew = relationship("Crew", back_populates="group_member_info")

class InsightPost(Base):
    __tablename__ = "insight_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    content = Column(String)
    tag = Column(String)  # [채용공고], [기술블로그], [기타]
    author_nickname = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
