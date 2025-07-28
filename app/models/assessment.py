from sqlalchemy import Column, Integer, DateTime, String, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
from enum import Enum


class AssessmentStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    TIMED_OUT = "timed_out"


class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey(
        "candidate_applications.application_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.test_id"), nullable=False)

    # Assessment status and progress
    status = Column(String(20), default=AssessmentStatus.STARTED.value)

    percentage_score = Column(Float, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Assessment report - JSON data containing detailed results
    # If null, indicates report has not been generated yet
    report = Column(JSON, nullable=True)

    # Relationships
    application = relationship(
        "CandidateApplication", back_populates="assessments")
    user = relationship("User")
    test = relationship("Test")
