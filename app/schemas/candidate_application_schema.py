from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CandidateApplicationBase(BaseModel):
    user_id: int
    test_id: int
    resume_link: str
    resume_text: Optional[str] = None
    parsed_resume: Optional[str] = None
    resume_score: Optional[int] = None
    skill_match_percentage: Optional[float] = None
    experience_score: Optional[int] = None
    education_score: Optional[int] = None
    ai_reasoning: Optional[str] = None
    is_shortlisted: Optional[bool] = None
    shortlist_reason: Optional[str] = None
    screening_completed_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CandidateApplicationCreate(BaseModel):
    email: str
    name: Optional[str] = None
    test_id: int
    resume_link: str
    # user_id is now optional and will be set after user creation/check
    user_id: Optional[int] = None

class CandidateApplicationBulkCreate(BaseModel):
    applications: List[CandidateApplicationCreate]

class CandidateApplicationResponse(CandidateApplicationBase):
    application_id: int
    class Config:
        from_attributes = True
        orm_mode = True

class CandidateApplicationBulkResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    success: int
    failed: int

class CandidateApplicationUpdate(BaseModel):
    resume_link: Optional[str] = None
    test_id: Optional[int] = None
    # Add other updatable fields as needed
    resume_text: Optional[str] = None
    parsed_resume: Optional[str] = None
    resume_score: Optional[int] = None
    skill_match_percentage: Optional[float] = None
    experience_score: Optional[int] = None
    education_score: Optional[int] = None
    ai_reasoning: Optional[str] = None
    is_shortlisted: Optional[bool] = None
    shortlist_reason: Optional[str] = None
    screening_completed_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
