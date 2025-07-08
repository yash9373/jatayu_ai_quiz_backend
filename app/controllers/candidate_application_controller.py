from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.candidate_application_service import CandidateApplicationService
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate, CandidateApplicationBulkCreate,
    CandidateApplicationResponse, CandidateApplicationBulkResponse
)
from app.db.database import get_db
from app.services.auth.auth_service import get_current_user
from app.models.user import UserRole

router = APIRouter()
service = CandidateApplicationService()

@router.post("/single", response_model=CandidateApplicationResponse)
async def process_single_application(
    data: CandidateApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    result = await service.process_single_application(db, data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/bulk", response_model=CandidateApplicationBulkResponse)
async def process_bulk_applications(
    data: CandidateApplicationBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    return await service.process_bulk_applications(db, data)
