#!/usr/bin/env python3
"""
Test utility for the enhanced scheduler
Run this to test scheduler functionality without starting the full scheduler
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

load_dotenv()

from app.models.test import Test, TestStatus
from app.models.candidate_application import CandidateApplication
from scheduler import TestScheduler

async def test_scheduler_functionality():
    """Test the scheduler functionality"""
    print(" Testing Enhanced Scheduler Functionality")
    print("=" * 50)
    
    # Initialize scheduler
    scheduler = TestScheduler(check_interval_seconds=10)
    
    # Create database connection
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\nCurrent Test Status Summary:")
        print("-" * 30)
        
        # Get all tests and their statuses
        result = await session.execute(select(Test))
        tests = result.scalars().all()
        
        status_counts = {}
        for test in tests:
            status = test.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Get candidate count for each test
            candidate_result = await session.execute(
                select(CandidateApplication).where(CandidateApplication.test_id == test.test_id)
            )
            candidates = candidate_result.scalars().all()
            shortlisted_count = sum(1 for c in candidates if c.is_shortlisted)
            
            print(f"Test {test.test_id}: {test.test_name[:30]}")
            print(f"  Status: {status}")
            print(f"  Candidates: {len(candidates)} total, {shortlisted_count} shortlisted")
            print(f"  Created: {test.created_at}")
            print(f"  Updated: {test.updated_at}")
            if test.scheduled_at:
                print(f"  Scheduled: {test.scheduled_at}")
            if test.assessment_deadline:
                print(f"  Deadline: {test.assessment_deadline}")
            print()
        
        print("📈 Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status.upper()}: {count} tests")
        
        print("\n Running Single Scheduler Cycle...")
        print("-" * 30)
        
        # Run a single scheduler cycle
        await scheduler.update_test_states()
        
        print("\n Scheduler test completed!")
        print("\nTo run the scheduler continuously, use:")
        print("python scheduler.py")

async def check_preparing_tests():
    """Check for tests that should transition from PREPARING to DRAFT"""
    print("\n🔍 Checking PREPARING Tests:")
    print("-" * 30)
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find PREPARING tests
        result = await session.execute(
            select(Test).where(Test.status == TestStatus.PREPARING.value)
        )
        preparing_tests = result.scalars().all()
        
        if not preparing_tests:
            print("No tests in PREPARING status found.")
            return
        
        for test in preparing_tests:
            # Count candidates
            candidate_result = await session.execute(
                select(CandidateApplication).where(CandidateApplication.test_id == test.test_id)
            )
            candidates = candidate_result.scalars().all()
            
            time_in_preparing = datetime.now(timezone.utc) - test.updated_at
            
            print(f"Test {test.test_id}: {test.test_name}")
            print(f"  Candidates: {len(candidates)}")
            print(f"  Time in PREPARING: {time_in_preparing}")
            print(f"  Should move to DRAFT: {'YES' if len(candidates) == 0 and time_in_preparing.total_seconds() > 600 else 'NO'}")
            print()

if __name__ == "__main__":
    print(" Enhanced Scheduler Test Utility")
    print("=" * 40)
    
    asyncio.run(test_scheduler_functionality())
    asyncio.run(check_preparing_tests())
