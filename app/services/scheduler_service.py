"""
Scheduler Service for Test Status Transitions
Industry-grade, modular, clean code
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.repositories.test_repo import TestRepository
from app.models.test import TestStatus
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

# Configure DB connection for scheduler
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/recruitment")
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(self.check_and_update_test_status, IntervalTrigger(minutes=1))
        self.scheduler.start()
        logger.info("Test status scheduler started.")

    async def check_and_update_test_status(self):
        async with AsyncSessionLocal() as session:
            repo = TestRepository(session)
            now = datetime.utcnow()
            # 1. Move scheduled → live
            scheduled_tests = await repo.get_scheduled_tests()
            for test in scheduled_tests:
                if test.scheduled_at and test.scheduled_at <= now and test.status == TestStatus.SCHEDULED.value:
                    test.status = TestStatus.LIVE.value
                    await session.commit()
                    logger.info(f"Test {test.test_id} moved to LIVE.")
            # 2. Move live → ended
            live_tests = await repo.get_live_tests()
            for test in live_tests:
                if test.assessment_deadline and now >= test.assessment_deadline:
                    test.status = TestStatus.ENDED.value
                    await session.commit()
                    logger.info(f"Test {test.test_id} moved to ENDED.")

scheduler_service = SchedulerService()

def start_scheduler():
    scheduler_service.start()
