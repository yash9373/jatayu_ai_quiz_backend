from pydantic import BaseModel

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    name: str  # Removed 'role' field

class UserResponse(BaseModel):
    uid: str
    email: str
    role: str
    name: str
    name: str
