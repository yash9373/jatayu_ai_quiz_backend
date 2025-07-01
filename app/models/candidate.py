from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from app.db.base import Base

class Candidate(Base):
    __tablename__ = "candidates"
    
    # Primary key that references user_id
    candidate_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True)
    
    # Resume content as text
    resume = Column(Text, nullable=True)
    
    # Parsed resume as JSON for structured data
    parsed_resume = Column(JSON, nullable=True)
    
    # Relationship to User table
    user = relationship("User", foreign_keys=[candidate_id])
