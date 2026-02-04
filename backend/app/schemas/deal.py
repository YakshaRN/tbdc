"""
Deal schemas for request/response validation.
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from decimal import Decimal


class DealBase(BaseModel):
    """Base deal schema with common fields."""
    
    Deal_Name: str = Field(..., description="Deal name (required)")
    Account_Name: Optional[Dict[str, Any]] = Field(None, description="Associated account")
    Contact_Name: Optional[Dict[str, Any]] = Field(None, description="Associated contact")
    Amount: Optional[float] = Field(None, description="Deal amount")
    Stage: Optional[str] = Field(None, description="Deal stage")
    Closing_Date: Optional[str] = Field(None, description="Expected closing date")
    Probability: Optional[int] = Field(None, description="Probability of closing (%)")
    Type: Optional[str] = Field(None, description="Deal type")
    Lead_Source: Optional[str] = Field(None, description="Lead source")
    Description: Optional[str] = Field(None, description="Deal description")
    
    # Custom fields for TBDC
    Industry: Optional[str] = Field(None, description="Industry vertical")
    Company_Website: Optional[str] = Field(None, description="Company website URL")
    Support_Required: Optional[str] = Field(None, description="Support required from TBDC")


class DealCreate(DealBase):
    """Schema for creating a new deal."""
    pass


class DealUpdate(BaseModel):
    """Schema for updating a deal (all fields optional)."""
    
    Deal_Name: Optional[str] = None
    Account_Name: Optional[Dict[str, Any]] = None
    Contact_Name: Optional[Dict[str, Any]] = None
    Amount: Optional[float] = None
    Stage: Optional[str] = None
    Closing_Date: Optional[str] = None
    Probability: Optional[int] = None
    Type: Optional[str] = None
    Lead_Source: Optional[str] = None
    Description: Optional[str] = None
    Industry: Optional[str] = None
    Company_Website: Optional[str] = None
    Support_Required: Optional[str] = None


class DealResponse(BaseModel):
    """Response schema for a single deal."""
    
    data: Dict[str, Any] = Field(..., description="Deal data from Zoho")
    
    class Config:
        extra = "allow"


class DealListResponse(BaseModel):
    """Response schema for a list of deals."""
    
    data: List[Dict[str, Any]] = Field(default_factory=list, description="List of deals")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Records per page")
    total_count: int = Field(0, description="Total number of records in this response")
    more_records: bool = Field(False, description="Whether more records are available")
