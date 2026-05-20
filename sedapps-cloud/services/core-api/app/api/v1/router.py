from fastapi import APIRouter

from app.api.v1 import auth, projects, articles, jobs, internal

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(articles.router, prefix="/projects", tags=["cms"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
