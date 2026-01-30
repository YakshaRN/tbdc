"""
FastAPI dependencies for dependency injection.
"""
from fastapi import Request, Depends, HTTPException
from loguru import logger

from app.services.zoho.crm_service import ZohoCRMService, zoho_crm_service
from app.services.zoho.token_manager import zoho_token_manager


async def get_zoho_token(request: Request) -> str:
    """
    Dependency to get Zoho access token from request state.
    
    The token is injected by ZohoTokenMiddleware.
    """
    token = getattr(request.state, "zoho_access_token", None)
    
    if not token:
        # Fallback: try to get token directly
        try:
            token = await zoho_token_manager.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get Zoho token: {e}")
            raise HTTPException(
                status_code=503,
                detail="Zoho service unavailable"
            )
    
    return token


async def get_zoho_service() -> ZohoCRMService:
    """
    Dependency to get Zoho CRM service instance.
    """
    return zoho_crm_service


def require_zoho_configured():
    """
    Dependency that ensures Zoho is properly configured.
    """
    if not zoho_token_manager.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Zoho CRM integration is not configured"
        )
    return True
