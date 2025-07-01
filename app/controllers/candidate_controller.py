from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.candidate_service import CandidateService
from app.services.Auth.auth_service import get_current_user
from app.schemas.candidate_schema import CandidateCreate, CandidateUpdate, CandidateResponse, CandidateSummary
from app.db.database import get_db
from app.models.user import User, UserRole

router = APIRouter()
candidate_service = CandidateService()

def recruiter_required(current_user: User = Depends(get_current_user)):
    """Only recruiters can access all candidate data"""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required"
        )
    return current_user

def candidate_or_recruiter(current_user: User = Depends(get_current_user)):
    """Candidates can manage their own profile, recruiters can view all"""
    return current_user

@router.post("/", response_model=CandidateResponse)
async def create_candidate_profile(
    candidate_data: CandidateCreate,
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """Create candidate profile - candidates can create their own, recruiters can create for anyone"""
    # If candidate, they can only create their own profile
    if current_user.role == UserRole.candidate and candidate_data.candidate_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidates can only create their own profile"
        )
    
    return await candidate_service.create_candidate_profile(candidate_data, db)

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate_profile(
    candidate_id: int,
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """Get candidate profile - candidates can view their own, recruiters can view all"""
    # Candidates can only view their own profile
    if current_user.role == UserRole.candidate and candidate_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    return await candidate_service.get_candidate_by_id(candidate_id, db)

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate_profile(
    candidate_id: int,
    update_data: CandidateUpdate,
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """Update candidate profile - candidates can update their own, recruiters can update any"""
    # Candidates can only update their own profile
    if current_user.role == UserRole.candidate and candidate_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    return await candidate_service.update_candidate_profile(candidate_id, update_data, db)

@router.delete("/{candidate_id}")
async def delete_candidate_profile(
    candidate_id: int,
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """Delete candidate profile - candidates can delete their own, recruiters can delete any"""
    # Candidates can only delete their own profile
    if current_user.role == UserRole.candidate and candidate_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own profile"
        )
    
    return await candidate_service.delete_candidate_profile(candidate_id, db)

@router.get("/", response_model=List[CandidateSummary])
async def list_candidates(
    current_user: User = Depends(recruiter_required),  # Only recruiters can list all candidates
    db: AsyncSession = Depends(get_db)
):
    """List all candidates (recruiter only)"""
    return await candidate_service.get_all_candidates(db)
