from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import test_repo
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse, TestSummary
from app.models.user import User, UserRole
import json

class TestService:
    
    async def create_test(self, test_data: TestCreate, created_by: int, db: AsyncSession) -> TestResponse:
        """Create a new test"""
        try:
            test = await test_repo.create_test(
                db=db,
                test_data=test_data.dict(),
                created_by=created_by
            )
            
            # Get the test with creator info
            test_with_creator = await test_repo.get_test_by_id(db, test.test_id)
            return self._format_test_response(test_with_creator)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create test: {str(e)}"
            )
    
    async def get_test_by_id(self, test_id: int, db: AsyncSession) -> TestResponse:
        """Get test by ID"""
        test = await test_repo.get_test_by_id(db, test_id)
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )
        return self._format_test_response(test)
    
    async def get_tests_by_creator(self, creator_id: int, db: AsyncSession) -> List[TestSummary]:
        """Get all tests created by a user"""
        tests = await test_repo.get_tests_by_creator(db, creator_id)
        return [self._format_test_summary(test) for test in tests]
    
    async def get_all_tests(self, skip: int = 0, limit: int = 100, db: AsyncSession = None) -> List[TestSummary]:
        """Get all tests with pagination"""
        tests = await test_repo.get_all_tests(db, skip, limit)
        return [self._format_test_summary(test) for test in tests]
    
    async def update_test(
        self, 
        test_id: int, 
        test_data: TestUpdate, 
        updated_by: int, 
        db: AsyncSession
    ) -> TestResponse:
        """Update a test (recruiters only - access control handled at controller level)"""
        
        # Get the test first
        existing_test = await test_repo.get_test_by_id(db, test_id)
        if not existing_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )
        
        try:
            updated_test = await test_repo.update_test(
                db=db,
                test_id=test_id,
                test_data=test_data.dict(exclude_unset=True),
                updated_by=updated_by
            )
            return self._format_test_response(updated_test)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update test: {str(e)}"
            )
    
    async def delete_test(self, test_id: int, db: AsyncSession) -> dict:
        """Delete a test (recruiters only - access control handled at controller level)"""
        
        # Get the test first
        existing_test = await test_repo.get_test_by_id(db, test_id)
        if not existing_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )
        
        success = await test_repo.delete_test(db, test_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete test"
            )
        
        return {"message": "Test deleted successfully"}
    
    def _format_test_response(self, test) -> TestResponse:
        """Format test with creator/updater info"""
        return TestResponse(
            test_id=test.test_id,
            test_name=test.test_name,
            job_description=test.job_description,
            parsed_job_description=json.loads(test.parsed_job_description) if test.parsed_job_description else None,
            skill_graph=json.loads(test.skill_graph) if test.skill_graph else None,
            created_by=test.created_by,
            updated_by=test.updated_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            scheduled_at=test.scheduled_at,
            creator_name=test.creator.name if test.creator else None,
            creator_role=test.creator.role if test.creator else None,
            updater_name=test.updater.name if test.updater else None,
            updater_role=test.updater.role if test.updater else None
        )
    
    def _format_test_summary(self, test) -> TestSummary:
        """Format test summary"""
        return TestSummary(
            test_id=test.test_id,
            test_name=test.test_name,
            created_by=test.created_by,
            creator_name=test.creator.name if test.creator else None,
            created_at=test.created_at,
            scheduled_at=test.scheduled_at
        )
