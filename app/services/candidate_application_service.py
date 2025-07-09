import os
import tempfile
import requests
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.repositories.test_repo import get_test_by_id
from app.models.candidate_application import CandidateApplication
from app.models.assessment import Assessment
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate, CandidateApplicationBulkCreate,
    CandidateApplicationResponse, CandidateApplicationBulkResponse
)
from datetime import datetime
from app.services.ai_screening_service import AIScreeningService
from sqlalchemy import insert
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.user_repo import get_user_by_email, create_user
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import random
import string

class CandidateApplicationService:
    def __init__(self):
        self.ai_service = AIScreeningService()

    async def process_single_application(self, db: AsyncSession, data: CandidateApplicationCreate) -> Dict[str, Any]:
        # Check or create user by email
        user = await get_user_by_email(db, data.email)
        generated_password = None
        if not user:
            # Generate random password
            generated_password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
            hashed_password = get_password_hash(generated_password)
            name = data.name or data.email.split('@')[0]
            new_user = await create_user(db, name=name, email=data.email, hashed_password=hashed_password, role=UserRole.candidate)
            user_id = new_user.user_id
        else:
            user_id = user.user_id
        # Check for duplicate
        existing = await CandidateApplicationRepository.get_by_user_and_test(db, user_id, data.test_id)
        if existing:
            return {"error": "Application already exists for this user and test."}
        # Download and extract resume
        resume_text = self._download_and_extract_resume(data.resume_link)
        # Fetch JD/skill graph from test table
        test = await get_test_by_id(db, data.test_id)
        if not test:
            return {"error": "Test not found."}
        # AI screening
        ai_result = self.ai_service.screen_resume_text(
            resume_text=resume_text,
            job_description=test.job_description,
            parsed_job_description=test.parsed_job_description,
            skill_graph=test.skill_graph
        )
        # Prepare DB data
        app_data = data.dict()
        app_data["user_id"] = user_id
        # Remove fields not in CandidateApplication model
        app_data.pop("email", None)
        app_data.pop("name", None)
        app_data.update({
            "resume_text": resume_text,
            "parsed_resume": ai_result.get("parsed_resume"),
            "resume_score": ai_result.get("resume_score"),
            "skill_match_percentage": ai_result.get("skill_match_percentage"),
            "experience_score": ai_result.get("experience_score"),
            "education_score": ai_result.get("education_score"),
            "ai_reasoning": ai_result.get("ai_reasoning"),
            "is_shortlisted": ai_result.get("is_shortlisted"),
            "applied_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "screening_completed_at": datetime.utcnow() if ai_result.get("resume_score") is not None else None
        })
        # Ensure parsed_resume is a string (JSON) if it's a dict
        if isinstance(app_data.get("parsed_resume"), dict):
            import json
            app_data["parsed_resume"] = json.dumps(app_data["parsed_resume"])
        application = await CandidateApplicationRepository.create_application(db, app_data)
        # Auto-shortlist logic: if enabled and shortlisted, insert into assessment
        if ai_result.get("is_shortlisted"):
            await self._insert_assessment(db, application)
        response = CandidateApplicationResponse.from_orm(application).dict()
        if generated_password:
            response["generated_password"] = generated_password
        return response

    async def process_bulk_applications(self, db: AsyncSession, bulk_data: CandidateApplicationBulkCreate) -> CandidateApplicationBulkResponse:
        results = []
        success = 0
        failed = 0
        for app in bulk_data.applications:
            try:
                result = await self.process_single_application(db, app)
                if "error" in result:
                    failed += 1
                else:
                    success += 1
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
                failed += 1
        return CandidateApplicationBulkResponse(results=results, total=len(bulk_data.applications), success=success, failed=failed)

    async def process_bulk_applications_concurrent(self, db: AsyncSession, bulk_data: CandidateApplicationBulkCreate, max_concurrent: int = 10) -> CandidateApplicationBulkResponse:
        import asyncio
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        success = 0
        failed = 0

        async def sem_task(app):
            async with semaphore:
                try:
                    result = await self.process_single_application(db, app)
                    return result
                except Exception as e:
                    return {"error": str(e)}

        tasks = [sem_task(app) for app in bulk_data.applications]
        all_results = await asyncio.gather(*tasks)
        for result in all_results:
            if "error" in result:
                failed += 1
            else:
                success += 1
            results.append(result)
        return CandidateApplicationBulkResponse(results=results, total=len(bulk_data.applications), success=success, failed=failed)

    def _download_and_extract_resume(self, resume_link: str) -> str:
        # Download PDF from Google Drive or direct link
        try:
            if 'drive.google.com' in resume_link:
                import re
                match = re.search(r'/d/([\w-]+)', resume_link)
                if match:
                    file_id = match.group(1)
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                else:
                    return "Error: Invalid Google Drive link."
            else:
                download_url = resume_link
            response = requests.get(download_url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            # Extract text
            text = self.ai_service.extract_text_from_file(tmp_file_path)
            os.remove(tmp_file_path)
            return text
        except Exception as e:
            return f"Error downloading or extracting resume: {e}"

    async def _insert_assessment(self, db: AsyncSession, application: CandidateApplication):
        await AssessmentRepository.insert_assessment(
            db,
            application_id=application.application_id,
            user_id=application.user_id,
            test_id=application.test_id
        )
