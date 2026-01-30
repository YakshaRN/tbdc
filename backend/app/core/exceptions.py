"""
Custom exception classes for the application.
"""
from fastapi import HTTPException, status


class ZohoAPIException(HTTPException):
    """Exception raised for Zoho API errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(status_code=status_code, detail=detail)


class ZohoTokenException(HTTPException):
    """Exception raised for Zoho token management errors."""
    
    def __init__(self, detail: str = "Failed to obtain valid Zoho access token"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class ZohoAuthenticationException(HTTPException):
    """Exception raised for Zoho authentication failures."""
    
    def __init__(self, detail: str = "Zoho authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class RateLimitException(HTTPException):
    """Exception raised when Zoho API rate limit is exceeded."""
    
    def __init__(self, detail: str = "Zoho API rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )
