from fastapi import APIRouter
from app.controllers import auth_controller
from app.controllers import test_controller
from app.controllers import assessment_controller
from app.controllers import candidate_controller

router = APIRouter()

router.include_router(auth_controller.router, prefix="/auth")
router.include_router(test_controller.router, prefix="/tests")
router.include_router(assessment_controller.router, prefix="/assessments")
router.include_router(candidate_controller.router, prefix="/candidates")