"""Main API router assembling all v1 sub-routers."""
from fastapi import APIRouter
from app.api.v1.students import router as students_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.documents import router as documents_router
from app.api.v1.programs import router as programs_router, advisor_router, cases_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(students_router)
api_router.include_router(recommendations_router)
api_router.include_router(documents_router)
api_router.include_router(programs_router)
api_router.include_router(advisor_router)
api_router.include_router(cases_router)
