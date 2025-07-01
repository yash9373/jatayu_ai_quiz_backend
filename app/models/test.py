from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Test(Base):
    __tablename__ = "test"
    
    # Primary key
    test_id = Column(Integer, primary_key=True, index=True)
    
    # Basic fields
    test_name = Column(String(100), nullable=False)
    job_description = Column(Text, nullable=True)  # Long job descriptions
    parsed_job_description = Column(Text, nullable=True)  # Stringified JSON
    skill_graph = Column(Text, nullable=True)  # Stringified JSON for skill graph
    
    # Foreign key relationships
    created_by = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("user.user_id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # When test is scheduled
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
