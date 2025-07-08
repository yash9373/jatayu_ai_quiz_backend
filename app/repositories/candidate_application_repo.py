from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from typing import Optional, List, Dict, Any
from app.models.candidate_application import CandidateApplication
from datetime import datetime

class CandidateApplicationRepository:
    @staticmethod
    async def create_application(db: AsyncSession, data: dict) -> CandidateApplication:
        application = CandidateApplication(**data)
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def get_by_user_and_test(db: AsyncSession, user_id: int, test_id: int) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(
                CandidateApplication.user_id == user_id,
                CandidateApplication.test_id == test_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_application(db: AsyncSession, application_id: int, update_data: dict) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            return None
        for k, v in update_data.items():
            setattr(application, k, v)
        application.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def get_by_id(db: AsyncSession, application_id: int) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def bulk_create(db: AsyncSession, data_list: List[dict]) -> List[CandidateApplication]:
        applications = [CandidateApplication(**data) for data in data_list]
        db.add_all(applications)
        await db.commit()
        for app in applications:
            await db.refresh(app)
        return applications

    @staticmethod
    async def delete_application(db: AsyncSession, application_id: int) -> bool:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            return False
        await db.delete(application)
        await db.commit()
        return True
