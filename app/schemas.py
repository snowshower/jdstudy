from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime

class CrewBase(BaseModel):
    nickname: str
    group_name: str
    survey_domains: Optional[str] = None
    survey_companies: Optional[str] = None

class CrewCreate(CrewBase):
    password: str = "1234"

class CrewResponse(BaseModel):
    id: int
    nickname: str
    group_name: str
    survey_domains: Optional[str]
    survey_companies: Optional[str]
    
    # helper for template rendering
    domain_list: list[str] = []
    company_list: list[str] = []

    @model_validator(mode='before')
    @classmethod
    def validate_from_model(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            # Convert comma-separated strings from DB back to lists for convenience
            domains = [d.strip() for d in data.survey_domains.split(",")] if data.survey_domains else []
            companies = [c.strip() for c in data.survey_companies.split(",")] if data.survey_companies else []
            return {
                "id": data.id,
                "nickname": data.nickname,
                "group_name": data.group_name,
                "survey_domains": data.survey_domains,
                "survey_companies": data.survey_companies,
                "domain_list": domains,
                "company_list": companies
            }
        return data

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    nickname: str
    password: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

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
    group_name: Optional[str] = None
    survey_domains: Optional[str] = None
    survey_companies: Optional[str] = None
