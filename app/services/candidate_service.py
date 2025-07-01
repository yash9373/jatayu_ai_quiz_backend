from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import candidate_repo
from app.repositories import user_repo
from app.schemas.candidate_schema import CandidateCreate, CandidateUpdate, CandidateResponse, CandidateSummary
from app.models.user import UserRole

class CandidateService:
    
    async def create_candidate_profile(self, candidate_data: CandidateCreate, db: AsyncSession) -> CandidateResponse:
        """Create a new candidate profile"""
        # Check if user exists and is a candidate
        user = await user_repo.get_user_by_id(db, candidate_data.candidate_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.role != UserRole.candidate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only candidate users can have candidate profiles"
            )
        
        # Check if candidate profile already exists
        existing_candidate = await candidate_repo.get_candidate_by_id(db, candidate_data.candidate_id)
        if existing_candidate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate profile already exists"
            )
        
        try:
            candidate = await candidate_repo.create_candidate(
                db=db,
                candidate_data=candidate_data.dict()
            )
            
            # Get with user relations for response
            candidate_with_user = await candidate_repo.get_candidate_by_id(db, candidate.candidate_id)
            return self._format_candidate_response(candidate_with_user)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create candidate profile: {str(e)}"
            )
    
    async def get_candidate_by_id(self, candidate_id: int, db: AsyncSession) -> CandidateResponse:
        """Get candidate profile by ID"""
        candidate = await candidate_repo.get_candidate_by_id(db, candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )
        return self._format_candidate_response(candidate)
    
    async def update_candidate_profile(self, candidate_id: int, update_data: CandidateUpdate, db: AsyncSession) -> CandidateResponse:
        """Update candidate profile"""
        existing_candidate = await candidate_repo.get_candidate_by_id(db, candidate_id)
        if not existing_candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )
        
        updated_candidate = await candidate_repo.update_candidate(
            db, candidate_id, update_data.dict(exclude_unset=True)
        )
        return self._format_candidate_response(updated_candidate)
    
    async def delete_candidate_profile(self, candidate_id: int, db: AsyncSession) -> dict:
        """Delete candidate profile"""
        success = await candidate_repo.delete_candidate(db, candidate_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )
        return {"message": "Candidate profile deleted successfully"}
    
    async def get_all_candidates(self, db: AsyncSession) -> List[CandidateSummary]:
        """Get all candidate profiles (for recruiters)"""
        candidates = await candidate_repo.get_all_candidates(db)
        return [self._format_candidate_summary(candidate) for candidate in candidates]
    
    def _format_candidate_response(self, candidate) -> CandidateResponse:
        """Convert database model to API response"""
        return CandidateResponse(
            candidate_id=candidate.candidate_id,
            resume=candidate.resume,
            parsed_resume=candidate.parsed_resume,
            # User information
            name=candidate.user.name if candidate.user else None,
            email=candidate.user.email if candidate.user else None,
            role=candidate.user.role if candidate.user else None
        )
    
    def _format_candidate_summary(self, candidate) -> CandidateSummary:
        """Convert to summary format"""
        return CandidateSummary(
            candidate_id=candidate.candidate_id,
            name=candidate.user.name if candidate.user else "Unknown",
            email=candidate.user.email if candidate.user else "Unknown",
            has_resume=bool(candidate.resume)
        )
