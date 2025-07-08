from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.test_service import TestService, get_enhanced_test_service
from app.services.auth.auth_service import get_current_user
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse, TestSummary
from app.db.database import get_db
from app.models.user import User, UserRole

router = APIRouter()
test_service = TestService()
enhanced_test_service = get_enhanced_test_service()

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
    """Create a new test with AI processing (recruiters only)"""
    return await enhanced_test_service.create_test_with_ai(
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
    return await test_service.get_all_tests(db=db, skip=skip, limit=limit)

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
async def get_test_by_id(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test by ID (owner only)"""
    test = await test_service.get_test_by_id(test_id=test_id, db=db)
    
    # Check if user is the owner
    if test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own tests"
        )
    
    return test

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test_data: TestUpdate,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Update a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tests"
        )
    
    return await test_service.update_test(
        test_id=test_id,
        test_data=test_data,
        updated_by=current_user.user_id,
        db=db
    )

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tests"
        )
    
    await test_service.delete_test(test_id=test_id, db=db)
    return {"message": "Test deleted successfully"}

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

# Additional endpoints for test lifecycle management

@router.get("/{test_id}", response_model=TestResponse)
async def get_test_by_id(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test by ID (owner only)"""
    test = await test_service.get_test_by_id(test_id=test_id, db=db)
    
    # Check if user is the owner
    if test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own tests"
        )
    
    return test

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test_data: TestUpdate,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Update a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tests"
        )
    
    return await test_service.update_test(
        test_id=test_id,
        test_data=test_data,
        updated_by=current_user.user_id,
        db=db
    )

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tests"
        )
    
    await test_service.delete_test(test_id=test_id, db=db)
    return {"message": "Test deleted successfully"}

@router.post("/{test_id}/schedule")
async def schedule_test(
    test_id: int,
    schedule_data: dict,  # Will contain scheduled_at and deadlines
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a test for publishing (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only schedule your own tests"
        )
    
    return await enhanced_test_service.schedule_test(
        test_id=test_id,
        schedule_data=schedule_data,
        db=db
    )

@router.post("/{test_id}/publish")
async def publish_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Manually publish a test immediately (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own tests"
        )
    
    return await enhanced_test_service.publish_test(test_id=test_id, db=db)

@router.post("/{test_id}/unpublish")
async def unpublish_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Unpublish/pause a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unpublish your own tests"
        )
    
    return await enhanced_test_service.unpublish_test(test_id=test_id, db=db)

@router.get("/{test_id}/status")
async def get_test_status(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Get test status and basic info (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own test status"
        )
    
    return await enhanced_test_service.get_test_status(test_id=test_id, db=db)

@router.post("/{test_id}/duplicate")
async def duplicate_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Create a copy of an existing test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only duplicate your own tests"
        )
    
    return await enhanced_test_service.duplicate_test(
        test_id=test_id,
        created_by=current_user.user_id,
        db=db
    )
