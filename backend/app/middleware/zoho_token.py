"""
Zoho Token Management Middleware.

This middleware ensures that a valid Zoho access token is available
for all requests that need to interact with Zoho APIs.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from loguru import logger

from app.services.zoho.token_manager import zoho_token_manager
from app.core.exceptions import ZohoTokenException


class ZohoTokenMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages Zoho OAuth tokens.
    
    Features:
    - Validates token availability before Zoho API routes
    - Attaches current access token to request state
    - Handles token refresh failures gracefully
    - Skips token validation for non-Zoho routes
    """
    
    # Routes that require Zoho token
    ZOHO_ROUTE_PREFIXES = [
        "/api/v1/zoho/",
        "/api/v1/leads/",
        "/api/v1/contacts/",
        "/api/v1/deals/",
    ]
    
    # Routes that should skip token validation
    EXCLUDED_ROUTES = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/zoho/",  # Auth routes handle tokens differently
    ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and ensure Zoho token availability.
        """
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip token validation for excluded routes
        if self._is_excluded_route(path):
            return await call_next(request)
        
        # Check if route requires Zoho token
        if self._requires_zoho_token(path):
            try:
                # Ensure token manager is configured
                if not zoho_token_manager.is_configured:
                    logger.warning(f"Zoho not configured for request: {path}")
                    return JSONResponse(
                        status_code=503,
                        content={
                            "detail": "Zoho CRM integration not configured",
                            "error": "zoho_not_configured"
                        }
                    )
                
                # Get valid access token and attach to request state
                access_token = await zoho_token_manager.get_access_token()
                request.state.zoho_access_token = access_token
                request.state.zoho_api_domain = zoho_token_manager.api_domain
                
                logger.debug(f"Zoho token attached for request: {path}")
                
            except ZohoTokenException as e:
                logger.error(f"Zoho token error for {path}: {e.detail}")
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "detail": e.detail,
                        "error": "zoho_token_error"
                    }
                )
            except Exception as e:
                logger.error(f"Unexpected error in Zoho middleware: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error during token validation",
                        "error": "internal_error"
                    }
                )
        
        # Proceed with request
        response = await call_next(request)
        return response
    
    def _requires_zoho_token(self, path: str) -> bool:
        """
        Check if the path requires a Zoho access token.
        """
        return any(path.startswith(prefix) for prefix in self.ZOHO_ROUTE_PREFIXES)
    
    def _is_excluded_route(self, path: str) -> bool:
        """
        Check if the path should skip token validation.
        """
        return any(path.startswith(route) for route in self.EXCLUDED_ROUTES)
