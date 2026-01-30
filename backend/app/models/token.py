"""
Token storage model for persisting OAuth tokens (optional).

This is useful if you want to persist tokens to database instead of memory.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ZohoToken(Base):
    """
    Model for storing Zoho OAuth tokens.
    
    Useful for:
    - Multi-instance deployments
    - Persisting tokens across restarts
    - Audit logging
    """
    __tablename__ = "zoho_tokens"
    
    id: str = Column(String(50), primary_key=True, default="default")
    access_token: str = Column(Text, nullable=False)
    refresh_token: str = Column(Text, nullable=False)
    token_type: str = Column(String(50), default="Bearer")
    expires_at: datetime = Column(DateTime, nullable=False)
    api_domain: Optional[str] = Column(String(255), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
