from fastapi import APIRouter

from app.api.v1 import account, admin, articles, auth, billing, content, credits, domains, internal, jobs, preview, projects

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(account.router, prefix="/account", tags=["account"])
api_router.include_router(credits.router, prefix="/credits", tags=["credits"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(articles.router, prefix="/projects", tags=["cms"])
api_router.include_router(content.router, prefix="/projects", tags=["content"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
api_router.include_router(preview.router, tags=["preview"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
