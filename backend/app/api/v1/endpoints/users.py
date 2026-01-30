"""
User authentication endpoints.

Handles user signup, login, and profile management.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from loguru import logger

from app.services.dynamodb.user_service import user_service
from app.core.security import create_access_token, get_token_data

router = APIRouter()


# Request/Response Models
class SignupRequest(BaseModel):
    """User signup request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    name: str = Field(..., min_length=2, description="User's full name")


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """User data response."""
    email: str
    name: str
    role: str


class AuthResponse(BaseModel):
    """Authentication response with token."""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserResponse] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password (min 6 characters)")


# Helper function to get current user from token
async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Extract and verify user from Authorization header."""
    if not authorization:
        return None
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    user_data = get_token_data(token)
    
    return user_data


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    
    Returns a JWT token upon successful signup.
    """
    try:
        result = user_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role="user"
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        user = result["user"]
        
        # Create JWT token
        token = create_access_token(data={
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        })
        
        logger.info(f"New user signed up: {request.email}")
        
        return AuthResponse(
            success=True,
            message="Account created successfully",
            token=token,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    """
    try:
        result = user_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not result["success"]:
            raise HTTPException(status_code=401, detail=result["error"])
        
        user = result["user"]
        
        # Create JWT token
        token = create_access_token(data={
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        })
        
        logger.info(f"User logged in: {request.email}")
        
        return AuthResponse(
            success=True,
            message="Login successful",
            token=token,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Get current user profile from token.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get fresh user data from database
    user_data = user_service.get_user(user["email"])
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"]
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: dict = Depends(get_current_user)
):
    """
    Change user password.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = user_service.change_password(
        email=user["email"],
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"success": True, "message": "Password changed successfully"}


@router.post("/verify-token")
async def verify_token(user: dict = Depends(get_current_user)):
    """
    Verify if the current token is valid.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "user": UserResponse(
            email=user["email"],
            name=user["name"],
            role=user["role"]
        )
    }
