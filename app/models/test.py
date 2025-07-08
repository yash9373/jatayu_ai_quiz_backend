from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from enum import Enum

class TestStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Test(Base):
    __tablename__ = "tests"
    
    # Primary key
    test_id = Column(Integer, primary_key=True, index=True)
    
    # Basic fields
    test_name = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)
    parsed_job_description = Column(Text, nullable=True)  # JSON string
    skill_graph = Column(Text, nullable=True)  # JSON string
    
    # Test configuration
    resume_score_threshold = Column(Integer, nullable=True)
    max_shortlisted_candidates = Column(Integer, nullable=True)
    auto_shortlist = Column(Boolean, default=False)
    total_questions = Column(Integer, nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)
    total_marks = Column(Integer, nullable=True)
    
    # Status and publishing
    status = Column(String(20), default=TestStatus.DRAFT.value)
    is_published = Column(Boolean, default=False)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    assessment_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
