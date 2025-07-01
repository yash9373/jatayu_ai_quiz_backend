from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import assessment_repo
from app.schemas.assessment_schema import AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentSummary
import json

class AssessmentService:
    
    async def start_assessment(self, assessment_data: AssessmentCreate, db: AsyncSession) -> AssessmentResponse:
        """Start a new assessment"""
        # Business rule: Check if candidate already has ongoing assessment for this test
        # (You might want to implement this check)
        
        try:
            assessment = await assessment_repo.create_assessment(
                db=db,
                assessment_data=assessment_data.dict()
            )
            
            # Get with related data for response
            assessment_with_relations = await assessment_repo.get_assessment_by_id(db, assessment.assessment_id)
            return self._format_assessment_response(assessment_with_relations)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to start assessment: {str(e)}"
            )
    
    async def get_assessment_by_id(self, assessment_id: int, db: AsyncSession) -> AssessmentResponse:
        """Get a specific assessment by ID"""
        assessment = await assessment_repo.get_assessment_by_id(db, assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        return self._format_assessment_response(assessment)
    
    async def update_assessment(self, assessment_id: int, update_data: AssessmentUpdate, db: AsyncSession) -> AssessmentResponse:
        """Update an assessment"""
        # First check if assessment exists
        existing_assessment = await assessment_repo.get_assessment_by_id(db, assessment_id)
        if not existing_assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Update the assessment
        updated_assessment = await assessment_repo.update_assessment(db, assessment_id, update_data.dict(exclude_unset=True))
        return self._format_assessment_response(updated_assessment)
    
    async def get_all_assessments(self, db: AsyncSession) -> List[AssessmentSummary]:
        """Get all assessments (for recruiters)"""
        assessments = await assessment_repo.get_all_assessments(db)
        return [self._format_assessment_summary(assessment) for assessment in assessments]
    
    async def get_assessments_for_candidate(self, candidate_id: int, db: AsyncSession) -> List[AssessmentSummary]:
        """Get assessments for a specific candidate"""
        assessments = await assessment_repo.get_assessments_by_candidate(db, candidate_id)
        return [self._format_assessment_summary(assessment) for assessment in assessments]
    
    def _format_assessment_summary(self, assessment) -> AssessmentSummary:
        """Convert to summary format"""
        return AssessmentSummary(
            assessment_id=assessment.assessment_id,
            started_at=assessment.started_at,
            test_name=assessment.test.test_name if assessment.test else "Unknown Test",
            candidate_name=assessment.candidate.name if assessment.candidate else "Unknown Candidate",
            score=assessment.score
        )
    
    def _format_assessment_response(self, assessment) -> AssessmentResponse:
        """Convert database model to API response"""
        return AssessmentResponse(
            assessment_id=assessment.assessment_id,
            started_at=assessment.started_at,
            test_id=assessment.test_id,
            candidate_id=assessment.candidate_id,
            remark=assessment.remark,
            resume_score=assessment.resume_score,
            skill_graph=json.loads(assessment.skill_graph) if assessment.skill_graph else None,
            score=assessment.score,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            # Related data
            test_name=assessment.test.test_name if assessment.test else None,
            candidate_name=assessment.candidate.name if assessment.candidate else None,
            candidate_email=assessment.candidate.email if assessment.candidate else None
        )