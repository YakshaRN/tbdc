"""
Security utilities for authentication.

Handles JWT token generation and validation.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from loguru import logger

from app.core.config import settings


# JWT Configuration
SECRET_KEY = settings.JWT_SECRET_KEY if hasattr(settings, 'JWT_SECRET_KEY') else "tbdc-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def get_token_data(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user data from token.
    
    Args:
        token: JWT token
        
    Returns:
        User data dict or None if invalid
    """
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    # Check expiration
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        return None
    
    return {
        "email": payload.get("email"),
        "name": payload.get("name"),
        "role": payload.get("role"),
    }
