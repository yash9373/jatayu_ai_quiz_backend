from fastapi import APIRouter
from app.controllers import auth_controller
from app.controllers import test_controller
from app.controllers import candidate_application_controller

router = APIRouter()

router.include_router(auth_controller.router, prefix="/auth")
router.include_router(test_controller.router, prefix="/tests")
router.include_router(candidate_application_controller.router, prefix="/candidate-applications")