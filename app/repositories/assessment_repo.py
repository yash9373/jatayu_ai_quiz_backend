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
