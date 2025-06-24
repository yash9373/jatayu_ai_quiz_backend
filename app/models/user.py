from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from app.db.base import Base
import enum

class UserRole(enum.Enum):
    candidate = "candidate"
    recruiter = "recruiter"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SqlEnum(UserRole), default=UserRole.candidate, nullable=False)
    name = Column(String)