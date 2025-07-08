from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.assessment_service import AssessmentService
from app.services.auth.auth_service import get_current_user
from app.schemas.assessment_schema import AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentSummary
from app.db.database import get_db
from app.models.user import User, UserRole

router = APIRouter()
assessment_service = AssessmentService()

def recruiter_required(current_user: User = Depends(get_current_user)):
    """Only recruiters can manage assessments"""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required"
        )
    return current_user

def candidate_or_recruiter(current_user: User = Depends(get_current_user)):
    """Candidates can view their own assessments, recruiters can view all"""
    return current_user

@router.post("/", response_model=AssessmentResponse)
async def start_assessment(
    assessment_data: AssessmentCreate,
    current_user: User = Depends(recruiter_required),  # Only recruiters start assessments
    db: AsyncSession = Depends(get_db)
):
    """Start a new assessment for a candidate"""
    return await assessment_service.start_assessment(assessment_data, db)

@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """Get assessment details"""
    assessment = await assessment_service.get_assessment_by_id(assessment_id, db)
    
    # Business rule: Candidates can only see their own assessments
    if current_user.role == UserRole.candidate and assessment.candidate_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own assessments"
        )
    
    return assessment

@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    update_data: AssessmentUpdate,
    current_user: User = Depends(recruiter_required),  # Only recruiters can update
    db: AsyncSession = Depends(get_db)
):
    """Update assessment details (recruiter only)"""
    return await assessment_service.update_assessment(assessment_id, update_data, db)

@router.get("/", response_model=List[AssessmentSummary])
async def list_assessments(
    current_user: User = Depends(candidate_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """List assessments - candidates see only their own, recruiters see all"""
    if current_user.role == UserRole.candidate:
        return await assessment_service.get_assessments_for_candidate(current_user.user_id, db)
    else:
        return await assessment_service.get_all_assessments(db)