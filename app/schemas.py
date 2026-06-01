from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime

class CrewBase(BaseModel):
    nickname: str
    desired_job: str
    companies: list[str] = []
    tech_stacks: list[str] = []

class CrewCreate(CrewBase):
    password: str

class CrewResponse(BaseModel):
    id: int
    nickname: str
    desired_job: str
    companies: list[str]
    tech_stacks: list[str]
    
    @model_validator(mode='before')
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            # Convert comma-separated strings from DB back to lists for API
            return {
                "id": data.id,
                "nickname": data.nickname,
                "desired_job": data.desired_job,
                "companies": data.companies.split(", ") if data.companies else [],
                "tech_stacks": data.tech_stacks.split(", ") if data.tech_stacks else []
            }
        return data

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    nickname: str
    password: str

class GroupMemberResponse(BaseModel):
    nickname: str
    desired_job: str
    companies: list[str]
    tech_stacks: list[str]
    
    @model_validator(mode='before')
    @classmethod
    def validate_from_model(cls, data: Any) -> Any:
        if hasattr(data, "crew"):
            crew = data.crew
            return {
                "nickname": crew.nickname,
                "desired_job": crew.desired_job,
                "companies": crew.companies.split(", ") if crew.companies else [],
                "tech_stacks": crew.tech_stacks.split(", ") if crew.tech_stacks else []
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
    companies: Optional[list[str]] = None
    tech_stacks: Optional[list[str]] = None

class MoveMemberRequest(BaseModel):
    crew_id: int
    new_group_id: int
