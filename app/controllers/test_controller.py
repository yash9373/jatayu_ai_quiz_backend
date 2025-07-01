from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.test_service import TestService
from app.services.Auth.auth_service import get_current_user
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse, TestSummary
from app.db.database import get_db
from app.models.user import User, UserRole

router = APIRouter()
test_service = TestService()

def recruiter_required(current_user: User = Depends(get_current_user)):
    """Dependency to ensure only recruiters can access certain endpoints"""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Recruiter access required"
        )
    return current_user

@router.post("/", response_model=TestResponse)
async def create_test(
    test_data: TestCreate,
    current_user: User = Depends(recruiter_required),  # Only recruiters can create tests
    db: AsyncSession = Depends(get_db)
):
    """Create a new test (recruiters only)"""
    return await test_service.create_test(
        test_data=test_data,
        created_by=current_user.user_id,
        db=db
    )

@router.get("/", response_model=List[TestSummary])
async def get_all_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get all tests with pagination (recruiters only)"""
    return await test_service.get_all_tests(skip=skip, limit=limit, db=db)

@router.get("/my-tests", response_model=List[TestSummary])
async def get_my_tests(
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get tests created by the current user (recruiters only)"""
    return await test_service.get_tests_by_creator(
        creator_id=current_user.user_id,
        db=db
    )

@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test by ID (recruiters only)"""
    return await test_service.get_test_by_id(test_id=test_id, db=db)

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test_data: TestUpdate,
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Update a test (recruiters only)"""
    return await test_service.update_test(
        test_id=test_id,
        test_data=test_data,
        updated_by=current_user.user_id,
        db=db
    )

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Delete a test (recruiters only)"""
    return await test_service.delete_test(
        test_id=test_id,
        db=db
    )

# Additional role-based endpoints

@router.get("/recruiter/all", response_model=List[TestSummary])
async def get_all_tests_for_recruiters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get all tests - recruiter view with additional permissions"""
    return await test_service.get_all_tests(skip=skip, limit=limit, db=db)
