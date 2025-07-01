from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from app.models.assessment import Assessment

async def create_assessment(db: AsyncSession, assessment_data: dict) -> Assessment:
    """Create a new assessment"""
    assessment = Assessment(
        test_id=assessment_data["test_id"],
        candidate_id=assessment_data["candidate_id"]
        # started_at is auto-set by database
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment

async def get_assessment_by_id(db: AsyncSession, assessment_id: int) -> Optional[Assessment]:
    """Get assessment with related test and candidate data"""
    result = await db.execute(
        select(Assessment)
        .options(
            joinedload(Assessment.test),      # Load test data too
            joinedload(Assessment.candidate)  # Load candidate data too
        )
        .where(Assessment.assessment_id == assessment_id)
    )
    return result.scalar_one_or_none()

async def update_assessment(db: AsyncSession, assessment_id: int, update_data: dict) -> Optional[Assessment]:
    """Update assessment with new data"""
    result = await db.execute(select(Assessment).where(Assessment.assessment_id == assessment_id))
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        return None
    
    # Update fields if provided
    if "remark" in update_data:
        assessment.remark = update_data["remark"]
    if "resume_score" in update_data:
        assessment.resume_score = update_data["resume_score"]
    if "skill_graph" in update_data:
        # Convert dict to JSON string
        assessment.skill_graph = json.dumps(update_data["skill_graph"]) if update_data["skill_graph"] else None
    if "score" in update_data:
        assessment.score = update_data["score"]
    
    await db.commit()
    await db.refresh(assessment)
    
    # Return with relations
    return await get_assessment_by_id(db, assessment_id)

async def get_all_assessments(db: AsyncSession) -> List[Assessment]:
    """Get all assessments with related data"""
    result = await db.execute(
        select(Assessment)
        .options(
            joinedload(Assessment.test),
            joinedload(Assessment.candidate)
        )
        .order_by(Assessment.created_at.desc())
    )
    return result.scalars().unique().all()

async def get_assessments_by_candidate(db: AsyncSession, candidate_id: int) -> List[Assessment]:
    """Get assessments for a specific candidate"""
    result = await db.execute(
        select(Assessment)
        .options(
            joinedload(Assessment.test),
            joinedload(Assessment.candidate)
        )
        .where(Assessment.candidate_id == candidate_id)
        .order_by(Assessment.created_at.desc())
    )
    return result.scalars().unique().all()