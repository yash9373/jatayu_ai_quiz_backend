from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from app.models.candidate import Candidate
from app.models.user import User

async def create_candidate(db: AsyncSession, candidate_data: dict) -> Candidate:
    """Create a new candidate profile"""
    candidate = Candidate(
        candidate_id=candidate_data["candidate_id"],
        resume=candidate_data.get("resume"),
        parsed_resume=candidate_data.get("parsed_resume")
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate

async def get_candidate_by_id(db: AsyncSession, candidate_id: int) -> Optional[Candidate]:
    """Get candidate with user information"""
    result = await db.execute(
        select(Candidate)
        .options(joinedload(Candidate.user))
        .where(Candidate.candidate_id == candidate_id)
    )
    return result.scalar_one_or_none()

async def get_all_candidates(db: AsyncSession) -> List[Candidate]:
    """Get all candidates with user information"""
    result = await db.execute(
        select(Candidate)
        .options(joinedload(Candidate.user))
        .order_by(Candidate.candidate_id)
    )
    return result.scalars().unique().all()

async def update_candidate(db: AsyncSession, candidate_id: int, update_data: dict) -> Optional[Candidate]:
    """Update candidate profile"""
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        return None
    
    # Update fields if provided
    if "resume" in update_data:
        candidate.resume = update_data["resume"]
    if "parsed_resume" in update_data:
        candidate.parsed_resume = update_data["parsed_resume"]
    
    await db.commit()
    await db.refresh(candidate)
    
    # Return with user relation
    return await get_candidate_by_id(db, candidate_id)

async def delete_candidate(db: AsyncSession, candidate_id: int) -> bool:
    """Delete candidate profile"""
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        return False
    
    await db.delete(candidate)
    await db.commit()
    return True

async def candidate_exists(db: AsyncSession, candidate_id: int) -> bool:
    """Check if candidate profile exists"""
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id)
    )
    return result.scalar_one_or_none() is not None
