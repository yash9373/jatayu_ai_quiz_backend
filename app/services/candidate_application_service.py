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
    CandidateApplicationResponse, CandidateApplicationBulkResponse,
    CandidateApplicationSummaryResponse
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
        # If test is in draft, move to preparing when first candidate applies
        if test.status == "draft":
            from app.repositories.test_repo import TestRepository
            await TestRepository(db).update_test_status(test.test_id, "preparing")
        # AI screening
        ai_result = self.ai_service.screen_resume_text(
            resume_text=resume_text,
            job_description=test.job_description,
            parsed_job_description=test.parsed_job_description,
            skill_graph=test.skill_graph,
            min_resume_score=test.resume_score_threshold if test.auto_shortlist else None
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
        
        # Prepare response with user information
        response_dict = {
            "application_id": application.application_id,
            "user_id": application.user_id,
            "test_id": application.test_id,
            "resume_link": application.resume_link,
            "resume_text": application.resume_text,
            "parsed_resume": application.parsed_resume,
            "resume_score": application.resume_score,
            "skill_match_percentage": application.skill_match_percentage,
            "experience_score": application.experience_score,
            "education_score": application.education_score,
            "ai_reasoning": application.ai_reasoning,
            "is_shortlisted": application.is_shortlisted,
            "shortlist_reason": application.shortlist_reason,
            "screening_completed_at": application.screening_completed_at,
            "notified_at": application.notified_at,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
            "candidate_name": data.name or data.email.split('@')[0],
            "candidate_email": data.email
        }
        
        if generated_password:
            response_dict["generated_password"] = generated_password
        return response_dict

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

    async def get_applications_by_test_id(self, db: AsyncSession, test_id: int) -> List[CandidateApplicationResponse]:
        """Get all candidate applications for a specific test."""
        applications = await CandidateApplicationRepository.get_applications_by_test_id(db, test_id)
        
        response_list = []
        for app in applications:
            # Convert to dict and add user information
            app_dict = {
                "application_id": app.application_id,
                "user_id": app.user_id,
                "test_id": app.test_id,
                "resume_link": app.resume_link,
                "resume_text": app.resume_text,
                "parsed_resume": app.parsed_resume,
                "resume_score": app.resume_score,
                "skill_match_percentage": app.skill_match_percentage,
                "experience_score": app.experience_score,
                "education_score": app.education_score,
                "ai_reasoning": app.ai_reasoning,
                "is_shortlisted": app.is_shortlisted,
                "shortlist_reason": app.shortlist_reason,
                "screening_completed_at": app.screening_completed_at,
                "notified_at": app.notified_at,
                "applied_at": app.applied_at,
                "updated_at": app.updated_at,
                "candidate_name": app.user.name if app.user else None,
                "candidate_email": app.user.email if app.user else None
            }
            response_list.append(CandidateApplicationResponse(**app_dict))
        
        return response_list

    async def get_applications_summary_by_test_id(self, db: AsyncSession, test_id: int) -> List[CandidateApplicationSummaryResponse]:
        """Get minimal summary of candidate applications for a specific test."""
        from app.schemas.candidate_application_schema import CandidateApplicationSummaryResponse
        applications = await CandidateApplicationRepository.get_applications_by_test_id_with_user(db, test_id)
        
        response_list = []
        for app in applications:
            app_dict = {
                "application_id": app.application_id,
                "user_id": app.user_id,
                "candidate_name": app.user.name if app.user else "Unknown",
                "candidate_email": app.user.email if app.user else "Unknown",
                "resume_link": app.resume_link,
                "resume_score": app.resume_score,
                "is_shortlisted": app.is_shortlisted
            }
            response_list.append(CandidateApplicationSummaryResponse(**app_dict))
        
        return response_list

    async def get_single_application_with_user(self, db: AsyncSession, application_id: int) -> Optional[CandidateApplicationResponse]:
        """Get a single application with full details including user information."""
        application = await CandidateApplicationRepository.get_application_with_user_by_id(db, application_id)
        if not application:
            return None
        
        return CandidateApplicationResponse(
            application_id=application.application_id,
            user_id=application.user_id,
            test_id=application.test_id,
            resume_link=application.resume_link,
            resume_text=application.resume_text,
            parsed_resume=application.parsed_resume,
            resume_score=application.resume_score,
            skill_match_percentage=application.skill_match_percentage,
            experience_score=application.experience_score,
            education_score=application.education_score,
            ai_reasoning=application.ai_reasoning,
            is_shortlisted=application.is_shortlisted,
            shortlist_reason=application.shortlist_reason,
            screening_completed_at=application.screening_completed_at,
            notified_at=application.notified_at,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
            candidate_name=application.user.name,
            candidate_email=application.user.email
        )

    async def shortlist_bulk_candidates(self, db: AsyncSession, test_id: int, min_score: int):
        from app.repositories.candidate_application_repo import CandidateApplicationRepository
        from app.services.notification_service import NotificationService
        # Get all applications for the test (with user info)
        applications = await CandidateApplicationRepository.get_applications_by_test_id_with_user(db, test_id)
        shortlisted = []
        notified_count = 0
        for app in applications:
            should_shortlist = app.resume_score is not None and app.resume_score >= min_score
            was_shortlisted = app.is_shortlisted
            app.is_shortlisted = should_shortlist
            db.add(app)
            if should_shortlist:
                shortlisted.append({
                    "candidate_email": app.user.email if app.user else None,
                    "resume_score": app.resume_score
                })
                # Notify only if newly shortlisted
                if not was_shortlisted:
                    try:
                        await NotificationService.notify_candidate_shortlisted(db, app)
                        notified_count += 1
                    except Exception:
                        pass
        await db.commit()
        return {
            "shortlisted": shortlisted,
            "notified": notified_count,
            "message": f"{notified_count} candidates shortlisted and notified."
        }
