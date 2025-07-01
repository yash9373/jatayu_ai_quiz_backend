from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.user import UserRole

class TestCreate(BaseModel):
    test_name: str = Field(..., max_length=100, description="Name of the test")
    job_description: Optional[str] = None
    parsed_job_description: Optional[Dict[str, Any]] = None  # Will be converted to JSON string
    skill_graph: Optional[Dict[str, Any]] = None  # Will be converted to JSON string
    scheduled_at: Optional[datetime] = None

class TestUpdate(BaseModel):
    test_name: Optional[str] = Field(None, max_length=100)
    job_description: Optional[str] = None
    parsed_job_description: Optional[Dict[str, Any]] = None
    skill_graph: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None

class TestResponse(BaseModel):
    test_id: int
    test_name: str
    job_description: Optional[str]
    parsed_job_description: Optional[Dict[str, Any]] = None  # Will be parsed from JSON string
    skill_graph: Optional[Dict[str, Any]] = None  # Will be parsed from JSON string
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime] = None
    
    # Creator and updater info
    creator_name: Optional[str] = None
    creator_role: Optional[UserRole] = None
    updater_name: Optional[str] = None
    updater_role: Optional[UserRole] = None
    
    class Config:
        from_attributes = True

class TestSummary(BaseModel):
    test_id: int
    test_name: str
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
