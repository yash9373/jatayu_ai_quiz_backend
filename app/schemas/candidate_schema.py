from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.user import UserRole

class CandidateCreate(BaseModel):
    """Schema for creating a candidate profile"""
    candidate_id: int = Field(..., description="User ID of the candidate")
    resume: Optional[str] = Field(None, description="Resume text content")
    parsed_resume: Optional[Dict[str, Any]] = Field(None, description="Structured resume data")

class CandidateUpdate(BaseModel):
    """Schema for updating candidate profile"""
    resume: Optional[str] = None
    parsed_resume: Optional[Dict[str, Any]] = None

class CandidateResponse(BaseModel):
    """Schema for candidate profile response"""
    candidate_id: int
    resume: Optional[str]
    parsed_resume: Optional[Dict[str, Any]]
    
    # Related user information
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    
    class Config:
        from_attributes = True

class CandidateSummary(BaseModel):
    """Lightweight candidate summary"""
    candidate_id: int
    name: str
    email: str
    has_resume: bool = False
    
    class Config:
        from_attributes = True
