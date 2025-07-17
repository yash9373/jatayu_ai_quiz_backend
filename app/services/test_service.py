from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import test_repo
from app.repositories.test_repo import TestRepository
from app.services.ai_service import get_ai_service
from app.services.notification_service import get_notification_service
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse, TestSummary, TestSchedule
from app.models.test import Test, TestStatus
from app.models.user import User
import json
import logging

logger = logging.getLogger(__name__)

class TestService:
    """Test Service with AI integration and notifications"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.notification_service = get_notification_service()
    
    async def create_test_with_ai(self, test_data: TestCreate, created_by: int, db: AsyncSession) -> TestResponse:
        """Create a new test with AI processing"""
        try:
            # 1. Create the test first
            repo = TestRepository(db)
            test = await repo.create_test(test_data, created_by)
            
            # 2. Get creator info for notifications
            creator = await self._get_user_by_id(created_by, db)
            
            # 3. Process job description with AI if provided
            if test_data.job_description:
                await self._process_job_description_with_ai(test, creator, db)
                # Fetch updated test data after AI processing
                test = await repo.get_test_by_id(test.test_id)
            
            # 4. Return test response
            return await self._format_test_response(test, creator)
            
        except Exception as e:
            logger.error(f"Error creating test with AI: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create test: {str(e)}"
            )
    
    async def _process_job_description_with_ai(self, test: Test, creator: User, db: AsyncSession) -> None:
        """Process job description with AI in background"""
        try:
            repo = TestRepository(db)
            
            # 1. Parse job description
            parsed_jd = await self.ai_service.parse_job_description(test.job_description)
            
            # 2. Generate skill graph
            skill_graph = await self.ai_service.generate_skill_graph(parsed_jd)
            
            # 3. Update test with AI results
            await repo.update_test_ai_data(test.test_id, parsed_jd, skill_graph)
            
            logger.info(f"AI processing completed for test {test.test_id}")
            
        except Exception as e:
            logger.error(f"AI processing failed for test {test.test_id}: {e}")
    
    async def schedule_test(self, test_id: int, schedule_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Schedule a test for publishing"""
        try:
            test_repo = TestRepository(db)
            
            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            creator = await self._get_user_by_id(test.created_by, db)
            
            # Update test with schedule info
            await test_repo.update_test_schedule(test_id, schedule_data)
            await test_repo.update_test_status(test_id, TestStatus.SCHEDULED.value)
            
            # Send notification
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_scheduled_notification(updated_test, creator)
            
            return {
                "message": "Test scheduled successfully",
                "test_id": test_id,
                "scheduled_at": schedule_data.get("scheduled_at"),
                "status": TestStatus.SCHEDULED.value
            }
            
        except Exception as e:
            logger.error(f"Error scheduling test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to schedule test: {str(e)}"
            )
    
    async def publish_test(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Manually publish a test"""
        try:
            test_repo = TestRepository(db)
            
            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            creator = await self._get_user_by_id(test.created_by, db)
            
            # Update test status
            await test_repo.update_test_status(test_id, TestStatus.PUBLISHED.value)
            await test_repo.update_is_published(test_id, True)
            
            # Send notification
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_published_notification(updated_test, creator)
            
            return {
                "message": "Test published successfully",
                "test_id": test_id,
                "status": TestStatus.PUBLISHED.value,
                "is_published": True
            }
            
        except Exception as e:
            logger.error(f"Error publishing test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to publish test: {str(e)}"
            )
    
    async def unpublish_test(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Unpublish/pause a test"""
        try:
            test_repo = TestRepository(db)
            
            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            creator = await self._get_user_by_id(test.created_by, db)
            
            # Update test status
            await test_repo.update_test_status(test_id, TestStatus.PAUSED.value)
            await test_repo.update_is_published(test_id, False)
            
            # Send notification
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_unpublished_notification(updated_test, creator)
            
            return {
                "message": "Test unpublished successfully",
                "test_id": test_id,
                "status": TestStatus.PAUSED.value,
                "is_published": False
            }
            
        except Exception as e:
            logger.error(f"Error unpublishing test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unpublish test: {str(e)}"
            )
    
    async def duplicate_test(self, test_id: int, created_by: int, db: AsyncSession) -> TestResponse:
        """Create a duplicate of an existing test"""
        try:
            test_repo = TestRepository(db)
            
            # Get original test
            original_test = await test_repo.get_test_by_id(test_id)
            if not original_test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            # Create duplicate test data
            duplicate_data = TestCreate(
                test_name=f"{original_test.test_name} (Copy)",
                job_description=original_test.job_description,
                resume_score_threshold=original_test.resume_score_threshold,
                max_shortlisted_candidates=original_test.max_shortlisted_candidates,
                auto_shortlist=original_test.auto_shortlist,
                total_questions=original_test.total_questions,
                time_limit_minutes=original_test.time_limit_minutes,
                total_marks=original_test.total_marks,
                scheduled_at=None,  # Reset scheduling
                application_deadline=None,
                assessment_deadline=None
            )
            
            # Create the duplicate
            duplicate_test = await test_repo.create_test(duplicate_data, created_by)
            
            # Copy AI-generated content if available
            if original_test.parsed_job_description:
                await test_repo.update_parsed_jd(duplicate_test.test_id, json.loads(original_test.parsed_job_description))
            
            if original_test.skill_graph:
                await test_repo.update_skill_graph(duplicate_test.test_id, json.loads(original_test.skill_graph))
            
            # Get creator and return response
            creator = await self._get_user_by_id(created_by, db)
            return await self._format_test_response(duplicate_test, creator)
            
        except Exception as e:
            logger.error(f"Error duplicating test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to duplicate test: {str(e)}"
            )
    
    async def get_test_status(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get test status information"""
        try:
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)
            
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            return {
                "test_id": test.test_id,
                "test_name": test.test_name,
                "status": test.status,
                "is_published": test.is_published,
                "scheduled_at": test.scheduled_at,
                "application_deadline": test.application_deadline,
                "assessment_deadline": test.assessment_deadline,
                "created_at": test.created_at,
                "updated_at": test.updated_at,
                "has_parsed_jd": test.parsed_job_description is not None,
                "has_skill_graph": test.skill_graph is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting test status {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get test status: {str(e)}"
            )
    
    async def get_all_tests(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TestResponse]:
        """Get all tests with pagination"""
        try:
            repo = TestRepository(db)
            tests = await repo.get_all_tests(skip=skip, limit=limit)
            
            # Format responses with creator info
            responses = []
            for test in tests:
                creator = await self._get_user_by_id(test.created_by, db)
                response = await self._format_test_response(test, creator)
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting all tests: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tests: {str(e)}"
            )
    
    async def get_tests_by_creator(self, creator_id: int, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TestResponse]:
        """Get tests created by a specific user"""
        try:
            repo = TestRepository(db)
            tests = await repo.get_tests_by_recruiter(recruiter_id=creator_id, skip=skip, limit=limit)
            
            # Get creator info once
            creator = await self._get_user_by_id(creator_id, db)
            
            # Format responses
            responses = []
            for test in tests:
                response = await self._format_test_response(test, creator)
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting tests by creator {creator_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tests: {str(e)}"
            )
    
    async def get_test_by_id(self, test_id: int, db: AsyncSession) -> TestResponse:
        """Get a test by ID"""
        try:
            repo = TestRepository(db)
            test = await repo.get_test_by_id(test_id)
            
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )
            
            # Get creator info
            creator = await self._get_user_by_id(test.created_by, db)
            
            return await self._format_test_response(test, creator)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get test: {str(e)}"
            )
    
    async def update_test(self, test_id: int, test_data: TestUpdate, updated_by: int, db: AsyncSession) -> TestResponse:
        """Update a test"""
        try:
            repo = TestRepository(db)
            
            # Check if test exists and user has permission
            test = await repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )
            
            # Update the test
            updated_test = await repo.update_test(test_id, test_data, updated_by)
            
            # Get creator info
            creator = await self._get_user_by_id(updated_test.created_by, db)
            
            # Send notification
            await self.notification_service.notify_test_updated(
                test_name=updated_test.test_name,
                test_id=test_id,
                recruiter_email=creator.email
            )
            
            return await self._format_test_response(updated_test, creator)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update test: {str(e)}"
            )
    
    async def delete_test(self, test_id: int, db: AsyncSession) -> Dict[str, str]:
        """Delete a test"""
        try:
            repo = TestRepository(db)
            
            # Check if test exists
            test = await repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )
            
            # Get creator info for notification
            creator = await self._get_user_by_id(test.created_by, db)
            
            # Delete the test
            await repo.delete_test(test_id)
            
            # Send notification
            await self.notification_service.notify_test_deleted(
                test_name=test.test_name,
                test_id=test_id,
                recruiter_email=creator.email
            )
            
            return {"message": "Test deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete test: {str(e)}"
            )

    async def _get_user_by_id(self, user_id: int, db: AsyncSession) -> User:
        """Get user by ID"""
        from app.repositories.user_repo import get_user_by_id
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    async def _format_test_response(self, test: Test, creator: User = None) -> TestResponse:
        """Format test response with creator info"""
        # Parse JSON fields
        parsed_jd = json.loads(test.parsed_job_description) if test.parsed_job_description else None
        skill_graph = json.loads(test.skill_graph) if test.skill_graph else None
        
        return TestResponse(
            test_id=test.test_id,
            test_name=test.test_name,
            job_description=test.job_description,
            parsed_job_description=parsed_jd,
            skill_graph=skill_graph,
            resume_score_threshold=test.resume_score_threshold,
            max_shortlisted_candidates=test.max_shortlisted_candidates,
            auto_shortlist=test.auto_shortlist,
            total_questions=test.total_questions,
            time_limit_minutes=test.time_limit_minutes,
            total_marks=test.total_marks,
            status=test.status,
            is_published=test.is_published,
            scheduled_at=test.scheduled_at,
            application_deadline=test.application_deadline,
            assessment_deadline=test.assessment_deadline,
            created_by=test.created_by,
            updated_by=test.updated_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            creator_name=creator.name if creator else None,
            creator_role=creator.role.value if creator else None
        )

# Service instance
test_service = TestService()

def get_test_service() -> TestService:
    """Get test service instance"""
    return test_service

# Alias for backward compatibility
def get_enhanced_test_service() -> TestService:
    """Get enhanced test service instance (alias)"""
    return test_service
