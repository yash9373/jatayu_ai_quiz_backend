from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.services.Auth.AuthInterface import IAuthService
from app.services.Auth.auth_service import AuthService, get_current_user
import app.schemas.user_schema as user_schema
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserRole

router = APIRouter()
auth_service: IAuthService = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login")
async def login(data: user_schema.UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.login(data.email, data.password, db)
    except HTTPException as e:
        raise e

@router.post("/register")
async def register(data: user_schema.UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        return {"user_id": await auth_service.signup(data.dict(), db)}
    except HTTPException as e:
        raise e

@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }

def recruiter_required(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return current_user

def candidate_required(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.candidate:
        raise HTTPException(status_code=403, detail="Candidate access required")
    return current_user

# Example protected endpoint for recruiters
@router.get("/recruiter-only")
async def recruiter_only_endpoint(current_user=Depends(recruiter_required)):
    return {"message": f"Hello Recruiter {current_user.name}"}

# Example protected endpoint for candidates
@router.get("/candidate-only")
async def candidate_only_endpoint(current_user=Depends(candidate_required)):
    return {"message": f"Hello Candidate {current_user.name}"}

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await auth_service.logout(token, db)
