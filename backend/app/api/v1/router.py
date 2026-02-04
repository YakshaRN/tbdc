"""
API v1 Router - aggregates all API routes.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import leads, deals, auth, zoho, marketing, web, settings, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Zoho Authentication"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(deals.router, prefix="/deals", tags=["Deals"])
api_router.include_router(zoho.router, prefix="/zoho", tags=["Zoho"])
api_router.include_router(marketing.router, prefix="/marketing", tags=["Marketing Materials"])
api_router.include_router(web.router, prefix="/web", tags=["Web Scraping"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
