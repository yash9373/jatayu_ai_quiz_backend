from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from sqlalchemy import select
from app.models.test import Test

router = APIRouter()
@router.post("/tests/{test_id}/assessment/add-candidate")
async def add_candidate_to_assessment(test_id: int, candidate_id: int, db: AsyncSession = Depends(get_db)):
    repo = AssessmentRepository(db)
    # Check if already exists
    existing = await repo.get_assessment_by_test_and_candidate(test_id, candidate_id)
    if existing:
        raise HTTPException(status_code=400, detail="Candidate already added to assessment for this test.")
    assessment = await repo.create_assessment(test_id=test_id, candidate_id=candidate_id)
    return {
        "assessment_id": assessment.assessment_id,
        "test_id": assessment.test_id,
        "candidate_id": assessment.candidate_id,
        "created_at": assessment.created_at,
        "message": "Candidate successfully added to assessment."
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.assessment_repo import AssessmentRepository
from app.db.database import get_db
from sqlalchemy import select
from app.models.test import Test

router = APIRouter()

@router.post("/{test_id}/shortlisted/assessments")
async def add_shortlisted_to_assessments(test_id: int, db: AsyncSession = Depends(get_db)):
    applications = await CandidateApplicationRepository.get_applications_by_test_id(db, test_id)
    shortlisted_apps = [app for app in applications if app.is_shortlisted]
    count = len(shortlisted_apps)
    if count == 0:
        raise HTTPException(status_code=404, detail="No shortlisted candidates found.")
    await AssessmentRepository.bulk_create_assessments(db, shortlisted_apps, test_id)
    return {
        "test_id": test_id,
        "shortlisted_count": count,
        "message": f"{count} shortlisted candidates added to assessments table."
    }

@router.get("/candidates/{candidate_id}/assessments")
async def get_assessments_for_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    assessments = await AssessmentRepository.get_assessments_by_candidate(db, candidate_id)
    response = []
    for a in assessments:
        test = None
        if a.test_id:
            result = await db.execute(select(Test).where(Test.test_id == a.test_id))
            test = result.scalar_one_or_none()
        response.append({
            "assessment_id": a.assessment_id,
            "test_id": a.test_id,
            "created_at": a.created_at,
            "test_name": test.test_name if test else None,
            "job_description": test.job_description if test else None,
            "scheduled_at": test.scheduled_at if test else None,
            "assessment_deadline": test.assessment_deadline if test else None,
            "status": test.status if test else None
        })
    return response
