# app/schemas/assessment_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AssessmentCreate(BaseModel):
    """What we need to START an assessment"""
    test_id: int = Field(..., description="Which test to take")
    candidate_id: int = Field(..., description="Which candidate is taking it")
    # Note: started_at will be auto-set to now()

class AssessmentUpdate(BaseModel):
    """What can be updated during/after assessment"""
    remark: Optional[str] = None
    resume_score: Optional[int] = Field(None, ge=0, le=100, description="Score 0-100")
    skill_graph: Optional[Dict[str, Any]] = None
    score: Optional[int] = Field(None, ge=0, le=100, description="Overall score 0-100")

class AssessmentResponse(BaseModel):
    """What we return when someone asks for assessment data"""
    assessment_id: int
    started_at: datetime
    test_id: int
    candidate_id: int
    remark: Optional[str]
    resume_score: Optional[int]
    skill_graph: Optional[Dict[str, Any]]  # Will be parsed from JSON
    score: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Related data - makes API more useful
    test_name: Optional[str] = None  # From test.test_name
    candidate_name: Optional[str] = None  # From user.name
    candidate_email: Optional[str] = None  # From user.email
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models

class AssessmentSummary(BaseModel):
    """Lighter version for listing assessments"""
    assessment_id: int
    started_at: datetime
    test_name: str
    candidate_name: str
    score: Optional[int]
    
    class Config:
        from_attributes = True