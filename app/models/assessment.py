from sqlalchemy import Column, Integer, DateTime
from app.db.base import Base
from datetime import datetime

class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer)
    user_id = Column(Integer)
    test_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
