
import asyncio
import os
import sys

from app import services
from app.repositories.candidate_application_repo import CandidateApplicationRepository
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
import os
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()
celery = Celery(
    "jatayu_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Update these with your actual DB connection string
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@celery.task
def screen_resume_task(application_id, resume_link, job_description, min_resume_score=None):
    import asyncio
    from app.services.ai_screening_service import AIScreeningService
    from app.repositories.candidate_application_repo import CandidateApplicationRepository
    from app.models.candidate_application import CandidateApplication
    from app.models.assessment import Assessment
load_dotenv()
celery = Celery(
    "jatayu_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Update these with your actual DB connection string
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@celery.task
def screen_resume_task(application_id, resume_link, job_description, min_resume_score=None):


    async def process():
        from app.services.ai_screening_service import AIScreeningService
        from app.models.candidate_application import CandidateApplication
        from app.models.assessment import Assessment
        import json
        service = AIScreeningService()
        async with AsyncSessionLocal() as db:
            # Download and extract resume
            resume_text = None
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
                import requests, tempfile, os
                response = requests.get(download_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name
                resume_text = service.extract_text_from_file(tmp_file_path)
                os.remove(tmp_file_path)
            except Exception as e:
                resume_text = f"Error downloading or extracting resume: {e}"

            # Run screening
            screening_result = service.screen_resume_text(resume_text, job_description, min_resume_score=min_resume_score)
            print("[Celery] screening_result:", screening_result)

            # Update CandidateApplication in DB with mapped AI output fields
            update_data = {
                "resume_text": resume_text,
                "parsed_resume": json.dumps(service._parse_resume_basic(resume_text)),
                "resume_score": screening_result.get("match_score"),
                "skill_match_percentage": screening_result.get("skills_match_score"),
                "experience_score": screening_result.get("experience_alignment_score"),
                "education_score": screening_result.get("certifications_score", screening_result.get("education_score", None)),
                "ai_reasoning": screening_result.get("reason"),
                "is_shortlisted": screening_result.get("is_shortlisted", False),
                "shortlist_reason": screening_result.get("shortlist_reason", None),
                "screening_completed_at": datetime.utcnow(),
                "screening_status": "completed"
            }
            print("[Celery] update_data:", update_data)
            await CandidateApplicationRepository.update_application(db, application_id, update_data)
    asyncio.run(process())
