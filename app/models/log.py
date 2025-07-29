from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    action = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    user = Column(String(255), nullable=True)
    entity = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
