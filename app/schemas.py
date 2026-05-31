from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime

class CrewBase(BaseModel):
    nickname: str
    desired_job: str
    target_company: Optional[str] = None
    interest_keywords: Optional[str] = None

class CrewCreate(CrewBase):
    password: str

class CrewResponse(CrewBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    nickname: str
    password: str

class GroupMemberResponse(BaseModel):
    nickname: str
    desired_job: str
    target_company: Optional[str] = None
    interest_keywords: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def validate_from_model(cls, data: Any) -> Any:
        if hasattr(data, "crew"):
            crew = data.crew
            return {
                "nickname": crew.nickname,
                "desired_job": crew.desired_job,
                "target_company": crew.target_company,
                "interest_keywords": crew.interest_keywords
            }
        return data
    model_config = ConfigDict(from_attributes=True)

class GroupResponse(BaseModel):
    id: int
    name: str
    common_companies: Optional[str] = None
    common_keywords: Optional[str] = None
    members: list[GroupMemberResponse]
    model_config = ConfigDict(from_attributes=True)

class MatchingResultResponse(BaseModel):
    groups: list[GroupResponse]

# Insight Board Schemas
class InsightPostBase(BaseModel):
    title: str
    link: str
    content: Optional[str] = None
    tag: Optional[str] = None

class InsightPostCreate(InsightPostBase):
    pass

class InsightPostUpdate(InsightPostBase):
    title: Optional[str] = None
    link: Optional[str] = None

class InsightPostResponse(InsightPostBase):
    id: int
    author_nickname: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# Admin Features Schemas
class CrewUpdateAdmin(BaseModel):
    target_company: Optional[str] = None
    interest_keywords: Optional[str] = None

class MoveMemberRequest(BaseModel):
    crew_id: int
    new_group_id: int
