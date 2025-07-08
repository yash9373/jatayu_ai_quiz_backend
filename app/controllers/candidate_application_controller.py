from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.candidate_application_service import CandidateApplicationService
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate, CandidateApplicationBulkCreate,
    CandidateApplicationResponse, CandidateApplicationBulkResponse, CandidateApplicationUpdate
)
from app.db.database import get_db
from app.services.auth.auth_service import get_current_user
from app.models.user import UserRole
from app.repositories.candidate_application_repo import CandidateApplicationRepository

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

@router.put("/{application_id}", response_model=CandidateApplicationResponse)
async def update_application(
    application_id: int,
    data: CandidateApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can update applications.")
    application = await CandidateApplicationRepository.update_application(db, application_id, data.dict(exclude_unset=True))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can delete applications.")
    deleted = await CandidateApplicationRepository.delete_application(db, application_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted successfully."}
