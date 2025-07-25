from celery import Celery

celery = Celery(
    "jatayu_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task
def screen_resume_task(resume_text, job_description, min_resume_score=None):
    from app.services.ai_screening_service import AIScreeningService
    service = AIScreeningService()
    return service.screen_resume_text(resume_text, job_description, min_resume_score=min_resume_score)
