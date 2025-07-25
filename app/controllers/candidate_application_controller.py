from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.candidate_application_service import CandidateApplicationService
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate, CandidateApplicationBulkCreate,
    CandidateApplicationResponse, CandidateApplicationBulkResponse, CandidateApplicationUpdate,
    CandidateApplicationSummaryResponse
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

@router.get("/test/{test_id}", response_model=List[CandidateApplicationSummaryResponse])
async def get_applications_by_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all candidate applications for a specific test - minimal response."""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    
    # Verify that the test exists and belongs to the current user
    from app.repositories.test_repo import get_test_by_id
    test = await get_test_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.created_by != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only view applications for tests you created")
    
    applications = await service.get_applications_summary_by_test_id(db, test_id)
    return applications

@router.get("/{application_id}", response_model=CandidateApplicationResponse)
async def get_single_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a single candidate application with full details."""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    
    application = await service.get_single_application_with_user(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if the application belongs to a test created by the current user
    from app.repositories.test_repo import get_test_by_id
    test = await get_test_by_id(db, application.test_id)
    if not test or test.created_by != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only view applications for tests you created")
    
    return application

@router.post("/shortlist-bulk")
async def shortlist_bulk_candidates(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    test_id = body.get("test_id")
    min_score = body.get("min_score")
    if not test_id or min_score is None:
        raise HTTPException(status_code=400, detail="test_id and min_score are required.")
    from app.services.candidate_application_service import CandidateApplicationService
    service = CandidateApplicationService()
    return await service.shortlist_bulk_candidates(db, test_id, min_score)
