from pydantic import BaseModel
from app.models.user import UserRole

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: UserRole
    
    class Config:
        from_attributes = True
