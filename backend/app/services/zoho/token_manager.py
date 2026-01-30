"""
Zoho OAuth Token Manager.

Handles automatic token refresh and provides valid access tokens for API calls.
Based on Zoho OAuth 2.0 documentation:
- Access tokens expire after 1 hour (3600 seconds)
- Refresh tokens do not expire
- Token refresh requires: refresh_token, client_id, client_secret, grant_type
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import ZohoTokenException


class ZohoTokenManager:
    """
    Manages Zoho OAuth tokens with automatic refresh.
    
    This manager:
    - Stores current access token in memory
    - Automatically refreshes token before expiry
    - Uses a lock to prevent race conditions during refresh
    - Provides thread-safe access to valid tokens
    """
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._api_domain: Optional[str] = None
        self._lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None
        self._refresh_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """
        Initialize the token manager.
        Creates HTTP client and fetches initial access token.
        """
        self._http_client = httpx.AsyncClient(timeout=30.0)
        
        # Get initial access token if refresh token is configured
        if settings.ZOHO_REFRESH_TOKEN:
            try:
                await self.refresh_access_token()
                logger.info("Zoho token manager initialized successfully")
                
                # Start background refresh task
                self._start_background_refresh()
            except Exception as e:
                logger.warning(f"Failed to initialize Zoho token: {e}")
        else:
            logger.warning("ZOHO_REFRESH_TOKEN not configured. Token manager inactive.")
    
    async def close(self) -> None:
        """
        Cleanup resources.
        """
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        
        if self._http_client:
            await self._http_client.aclose()
            logger.info("Zoho token manager closed")
    
    def _start_background_refresh(self) -> None:
        """
        Start a background task that refreshes the token before expiry.
        """
        async def refresh_loop():
            while True:
                try:
                    # Wait until token needs refresh
                    if self._token_expiry:
                        # Refresh 5 minutes before expiry
                        refresh_at = self._token_expiry - timedelta(
                            seconds=settings.ZOHO_TOKEN_REFRESH_BUFFER
                        )
                        wait_seconds = (refresh_at - datetime.utcnow()).total_seconds()
                        
                        if wait_seconds > 0:
                            logger.debug(f"Next token refresh in {wait_seconds:.0f} seconds")
                            await asyncio.sleep(wait_seconds)
                    
                    await self.refresh_access_token()
                    logger.info("Background token refresh completed")
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Background token refresh failed: {e}")
                    # Retry after 60 seconds on failure
                    await asyncio.sleep(60)
        
        self._refresh_task = asyncio.create_task(refresh_loop())
    
    async def refresh_access_token(self) -> str:
        """
        Refresh the access token using the refresh token.
        
        POST to {Accounts_URL}/oauth/v2/token with:
        - refresh_token
        - client_id
        - client_secret
        - grant_type: "refresh_token"
        
        Returns:
            str: New access token
            
        Raises:
            ZohoTokenException: If token refresh fails
        """
        async with self._lock:
            logger.debug("Refreshing Zoho access token...")
            
            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=30.0)
            
            token_url = f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/token"
            
            payload = {
                "refresh_token": settings.ZOHO_REFRESH_TOKEN,
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "grant_type": "refresh_token",
            }
            
            try:
                response = await self._http_client.post(
                    token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token refresh failed: {response.status_code} - {error_detail}")
                    raise ZohoTokenException(
                        f"Failed to refresh token: {response.status_code}"
                    )
                
                data = response.json()
                
                if "error" in data:
                    logger.error(f"Zoho token error: {data.get('error')}")
                    raise ZohoTokenException(f"Zoho error: {data.get('error')}")
                
                self._access_token = data["access_token"]
                self._api_domain = data.get("api_domain", settings.ZOHO_API_BASE_URL)
                
                # Calculate expiry (default 3600 seconds = 1 hour)
                expires_in = data.get("expires_in", 3600)
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info(
                    f"Token refreshed successfully. Expires at: {self._token_expiry}"
                )
                logger.debug(f"Access token: {self._access_token}")
                
                return self._access_token
                
            except httpx.RequestError as e:
                logger.error(f"HTTP error during token refresh: {e}")
                raise ZohoTokenException(f"Network error: {str(e)}")
    
    async def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
            
        Raises:
            ZohoTokenException: If unable to obtain valid token
        """
        # Check if token exists and is still valid
        if self._access_token and self._token_expiry:
            # Add buffer time before expiry
            buffer_time = timedelta(seconds=settings.ZOHO_TOKEN_REFRESH_BUFFER)
            if datetime.utcnow() < (self._token_expiry - buffer_time):
                return self._access_token
        
        # Token missing or expired, refresh it
        return await self.refresh_access_token()
    
    @property
    def api_domain(self) -> str:
        """
        Get the API domain for Zoho API calls.
        """
        return self._api_domain or settings.ZOHO_API_BASE_URL
    
    @property
    def is_configured(self) -> bool:
        """
        Check if Zoho credentials are configured.
        """
        return bool(
            settings.ZOHO_CLIENT_ID
            and settings.ZOHO_CLIENT_SECRET
            and settings.ZOHO_REFRESH_TOKEN
        )
    
    @property
    def token_status(self) -> dict:
        """
        Get current token status for debugging/monitoring.
        """
        return {
            "configured": self.is_configured,
            "has_token": bool(self._access_token),
            "expiry": self._token_expiry.isoformat() if self._token_expiry else None,
            "api_domain": self._api_domain,
            "is_valid": (
                self._access_token is not None
                and self._token_expiry is not None
                and datetime.utcnow() < self._token_expiry
            ),
        }


# Singleton instance
zoho_token_manager = ZohoTokenManager()
