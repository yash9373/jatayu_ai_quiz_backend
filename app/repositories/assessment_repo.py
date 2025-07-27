from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from app.models.assessment import Assessment
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AssessmentRepository:
    """Repository for Assessment entity operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assessment_instance(
        self,
        application_id: int,
        user_id: int,
        test_id: int
    ) -> Optional[int]:
        """
        Create a new assessment instance when a candidate starts taking a test

        Args:
            application_id: Candidate application ID
            user_id: User taking the assessment  
            test_id: Test blueprint ID

        Returns:
            assessment_id if successful, None otherwise
        """
        try:
            # Create new assessment instance
            assessment = Assessment(
                application_id=application_id,
                user_id=user_id,
                test_id=test_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(assessment)
            await self.db.commit()
            await self.db.refresh(assessment)

            # Get the actual ID value from the refreshed object
            assessment_id = getattr(assessment, 'assessment_id')
            logger.info(
                f"Created assessment instance {assessment_id} for user {user_id}, test {test_id}")
            return assessment_id

        except SQLAlchemyError as e:
            logger.error(
                f"Database error creating assessment instance: {str(e)}")
            await self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Error creating assessment instance: {str(e)}")
            await self.db.rollback()
            return None

    async def get_assessment_by_id(self, assessment_id: int) -> Optional[Assessment]:
        """Get assessment by ID"""
        try:
            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.assessment_id == assessment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error fetching assessment {assessment_id}: {str(e)}")
            return None

    async def get_user_assessment_for_test(self, user_id: int, test_id: int) -> Optional[Assessment]:
        """Check if user already has an assessment instance for this test"""
        try:
            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.user_id == user_id,
                    Assessment.test_id == test_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error checking existing assessment for user {user_id}, test {test_id}: {str(e)}")
            return None

    async def update_assessment_status(
        self,
        assessment_id: int,
        status: str,
        percentage_score: float,
        end_time: Optional[datetime] = None
    ) -> bool:
        """
        Update assessment with completion status and results

        Args:
            assessment_id: The assessment ID to update
            status: Assessment status string (e.g., "completed")
            percentage_score: Final percentage score for the assessment
            end_time: Optional end time for the assessment

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Prepare update values
            update_values = {
                "status": status,
                "percentage_score": percentage_score,
                "updated_at": datetime.utcnow()
            }

            # Add end_time if provided
            if end_time:
                update_values["end_time"] = end_time

            # Update assessment record using SQLAlchemy update statement
            stmt = update(Assessment).where(
                Assessment.assessment_id == assessment_id
            ).values(**update_values)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            logger.error(
                f"Error updating assessment {assessment_id}: {str(e)}")
            await self.db.rollback()
            return False

    @staticmethod
    async def insert_assessment(db: AsyncSession, application_id: int, user_id: int, test_id: int):
        """Legacy method - kept for backward compatibility"""
        stmt = insert(Assessment).values(
            application_id=application_id,
            user_id=user_id,
            test_id=test_id,
            created_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def bulk_create_assessments(db: AsyncSession, applications: list, test_id: int):
        from sqlalchemy import select
        for app in applications:
            user_id = app.user_id
            application_id = app.application_id
            exists = await db.execute(
                select(Assessment).where(Assessment.user_id ==
                                         user_id, Assessment.test_id == test_id)
            )
            if not exists.scalar():
                stmt = insert(Assessment).values(user_id=user_id,
                                                 test_id=test_id, application_id=application_id)
                await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_assessments_by_candidate(db: AsyncSession, user_id: int):
        from sqlalchemy import select
        result = await db.execute(
            select(Assessment).where(Assessment.user_id == user_id)
        )
        return result.scalars().all()

    async def is_assessment_completed(self, user_id: int, test_id: int) -> bool:
        """
        Check if user already has a completed assessment for this test

        Args:
            user_id: User ID to check
            test_id: Test ID to check

        Returns:
            bool: True if user has a completed assessment, False otherwise
        """
        try:
            from app.models.assessment import AssessmentStatus

            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.user_id == user_id,
                    Assessment.test_id == test_id,
                    Assessment.status == AssessmentStatus.COMPLETED.value
                )
            )
            completed_assessment = result.scalar_one_or_none()
            return completed_assessment is not None

        except Exception as e:
            logger.error(
                f"Error checking completed assessment for user {user_id}, test {test_id}: {str(e)}")
            return False
