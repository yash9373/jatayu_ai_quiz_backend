from fastapi import APIRouter
from app.controllers import auth_controller
# from app.controllers import recruiter_controller  # <-- comment or remove this line

router = APIRouter()

router.include_router(auth_controller.router, prefix="/auth")
# router.include_router(recruiter_controller.router, prefix="/recruiters")  # <-- comment or remove this line