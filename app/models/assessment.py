from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Assessment(Base):
    __tablename__ = "assessment"
    
    # Primary key
    assessment_id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    test_id = Column(Integer, ForeignKey("tests.test_id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Assessment data
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    remark = Column(Text, nullable=True)
    resume_score = Column(Integer, nullable=True)
    skill_graph = Column(Text, nullable=True)  # JSON string
    score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    test = relationship("Test", foreign_keys=[test_id])
    candidate = relationship("User", foreign_keys=[candidate_id])