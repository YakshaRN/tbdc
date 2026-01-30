"""
Authentication endpoints for Zoho OAuth flow.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger

from app.core.config import settings
from app.services.zoho.token_manager import zoho_token_manager

router = APIRouter()


@router.get("/zoho/authorize")
async def zoho_authorize():
    """
    Initiate Zoho OAuth authorization flow.
    
    Redirects user to Zoho's authorization page.
    """
    # Zoho OAuth scopes for CRM access
    scopes = [
        "ZohoCRM.modules.ALL",
        "ZohoCRM.settings.ALL",
        "ZohoCRM.users.ALL",
    ]
    
    auth_url = (
        f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/auth"
        f"?response_type=code"
        f"&client_id={settings.ZOHO_CLIENT_ID}"
        f"&scope={','.join(scopes)}"
        f"&redirect_uri={settings.ZOHO_REDIRECT_URI}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/zoho/callback")
async def zoho_callback(
    code: str = Query(None, description="Authorization code from Zoho"),
    error: str = Query(None, description="Error from Zoho"),
):
    """
    Handle Zoho OAuth callback.
    
    Exchanges authorization code for access and refresh tokens.
    
    Note: This endpoint is for initial setup. The refresh token should
    be saved to your environment configuration.
    """
    if error:
        logger.error(f"Zoho OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"Zoho OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    # Exchange code for tokens
    import httpx
    
    token_url = f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/token"
    
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code != 200:
        logger.error(f"Token exchange failed: {response.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {response.text}"
        )
    
    data = response.json()
    
    if "error" in data:
        raise HTTPException(status_code=400, detail=data.get("error"))
    
    # Return tokens (in production, store refresh_token securely)
    return {
        "message": "Authorization successful",
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
        "api_domain": data.get("api_domain"),
        "note": "Save the refresh_token to your ZOHO_REFRESH_TOKEN environment variable",
    }


@router.get("/zoho/status")
async def zoho_status():
    """
    Get current Zoho authentication status.
    """
    return {
        "configured": zoho_token_manager.is_configured,
        "token_status": zoho_token_manager.token_status,
    }
