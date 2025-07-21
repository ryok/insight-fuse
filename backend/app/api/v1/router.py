from fastapi import APIRouter
from app.api.v1.endpoints import articles, summaries, analyses, fetch, custom_sites
from app.api import gmail

api_router = APIRouter()

api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(fetch.router, prefix="/fetch", tags=["fetch"])
api_router.include_router(custom_sites.router, prefix="/custom-sites", tags=["custom-sites"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["gmail"])