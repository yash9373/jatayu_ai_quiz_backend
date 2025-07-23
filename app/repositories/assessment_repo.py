from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.models.assessment import Assessment
from datetime import datetime

class AssessmentRepository:
    @staticmethod
    async def insert_assessment(db: AsyncSession, application_id: int, user_id: int, test_id: int):
        stmt = insert(Assessment).values(
            application_id=application_id,
            user_id=user_id,
            test_id=test_id,
            shortlisted_at=datetime.utcnow()
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
                select(Assessment).where(Assessment.user_id == user_id, Assessment.test_id == test_id)
            )
            if not exists.scalar():
                stmt = insert(Assessment).values(user_id=user_id, test_id=test_id, application_id=application_id)
                await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_assessments_by_candidate(db: AsyncSession, user_id: int):
        from sqlalchemy import select
        result = await db.execute(
            select(Assessment).where(Assessment.user_id == user_id)
        )
        return result.scalars().all()
