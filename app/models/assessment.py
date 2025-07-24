from sqlalchemy import Column, Integer, DateTime, String, Float, Text, ForeignKey
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
    questions_answered = Column(Integer, default=0)
    total_questions = Column(Integer, nullable=True)
    current_question_index = Column(Integer, default=0)

    # Scoring
    total_score = Column(Float, default=0.0)
    max_possible_score = Column(Float, nullable=True)
    percentage_score = Column(Float, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    time_taken_minutes = Column(Integer, nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)

    # Results and data
    # JSON string of question-answer pairs
    answers_data = Column(Text, nullable=True)
    # JSON string of skill-wise performance
    skill_assessment_data = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    application = relationship(
        "CandidateApplication", back_populates="assessments")
    user = relationship("User")
    test = relationship("Test")
