from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.test import Test
from app.models.user import User
import json

async def create_test(db: AsyncSession, test_data: dict, created_by: int) -> Test:
    """Create a new test"""
    test = Test(
        test_name=test_data["test_name"],
        job_description=test_data.get("job_description"),
        parsed_job_description=json.dumps(test_data["parsed_job_description"]) if test_data.get("parsed_job_description") else None,
        skill_graph=json.dumps(test_data["skill_graph"]) if test_data.get("skill_graph") else None,
        scheduled_at=test_data.get("scheduled_at"),
        created_by=created_by
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test

async def get_test_by_id(db: AsyncSession, test_id: int) -> Optional[Test]:
    """Get test by ID with creator and updater info"""
    result = await db.execute(
        select(Test)
        .options(
            joinedload(Test.creator),
            joinedload(Test.updater)
        )
        .where(Test.test_id == test_id)
    )
    return result.scalar_one_or_none()

async def get_tests_by_creator(db: AsyncSession, creator_id: int) -> List[Test]:
    """Get all tests created by a specific user"""
    result = await db.execute(
        select(Test)
        .options(joinedload(Test.creator))
        .where(Test.created_by == creator_id)
        .order_by(Test.created_at.desc())
    )
    return result.scalars().all()

async def get_all_tests(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Test]:
    """Get all tests with pagination"""
    result = await db.execute(
        select(Test)
        .options(
            joinedload(Test.creator),
            joinedload(Test.updater)
        )
        .offset(skip)
        .limit(limit)
        .order_by(Test.created_at.desc())
    )
    return result.scalars().all()

async def update_test(db: AsyncSession, test_id: int, test_data: dict, updated_by: int) -> Optional[Test]:
    """Update an existing test"""
    result = await db.execute(select(Test).where(Test.test_id == test_id))
    test = result.scalar_one_or_none()
    
    if not test:
        return None
    
    # Update fields if provided
    if "test_name" in test_data and test_data["test_name"] is not None:
        test.test_name = test_data["test_name"]
    if "job_description" in test_data:
        test.job_description = test_data["job_description"]
    if "parsed_job_description" in test_data:
        test.parsed_job_description = json.dumps(test_data["parsed_job_description"]) if test_data["parsed_job_description"] else None
    if "skill_graph" in test_data:
        test.skill_graph = json.dumps(test_data["skill_graph"]) if test_data["skill_graph"] else None
    if "scheduled_at" in test_data:
        test.scheduled_at = test_data["scheduled_at"]
    
    test.updated_by = updated_by
    
    await db.commit()
    await db.refresh(test)
    return test

async def delete_test(db: AsyncSession, test_id: int) -> bool:
    """Delete a test"""
    result = await db.execute(select(Test).where(Test.test_id == test_id))
    test = result.scalar_one_or_none()
    
    if not test:
        return False
    
    await db.delete(test)
    await db.commit()
    return True
