# scheduler.py


import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from datetime import datetime, timezone
from app.repositories.test_repo import TestRepository
from app.models.test import TestStatus
from app.db.database import AsyncSessionLocal
from sqlalchemy import select, or_, and_

async def update_test_states():
    async with AsyncSessionLocal() as session:
        repo = TestRepository(session)
        now = datetime.now(timezone.utc)

        # Get all scheduled tests that should go live
        from app.models.test import Test
        scheduled_stmt = select(Test).where(
            and_(
                Test.status == TestStatus.SCHEDULED.value,
                Test.scheduled_at <= now,
                Test.assessment_deadline > now
            )
        )
        scheduled_result = await session.execute(scheduled_stmt)
        scheduled_tests = scheduled_result.scalars().all()
        for test in scheduled_tests:
            await repo.update_test_status(test.test_id, TestStatus.LIVE.value, is_published=True)
            print(f"[Scheduler] Test {test.test_id} moved to LIVE at {now}")

        # Get all live or scheduled tests that should end
        ending_stmt = select(Test).where(
            and_(
                or_(Test.status == TestStatus.SCHEDULED.value,
                    Test.status == TestStatus.LIVE.value),
                Test.assessment_deadline <= now
            )
        )
        ending_result = await session.execute(ending_stmt)
        ending_tests = ending_result.scalars().all()
        for test in ending_tests:
            await repo.update_test_status(test.test_id, TestStatus.ENDED.value)
            print(f"[Scheduler] Test {test.test_id} moved to ENDED at {now}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_test_states, 'interval', seconds=5)
    scheduler.start()
    print("[Scheduler] Started async test state updater.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())
