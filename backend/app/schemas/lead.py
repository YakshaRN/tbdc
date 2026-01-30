"""
Lead schemas for request/response validation.
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field


class LeadBase(BaseModel):
    """Base lead schema with common fields."""
    
    First_Name: Optional[str] = Field(None, description="Lead's first name")
    Last_Name: str = Field(..., description="Lead's last name (required)")
    Email: Optional[EmailStr] = Field(None, description="Lead's email address")
    Phone: Optional[str] = Field(None, description="Lead's phone number")
    Mobile: Optional[str] = Field(None, description="Lead's mobile number")
    Company: Optional[str] = Field(None, description="Lead's company name")
    Title: Optional[str] = Field(None, description="Lead's job title")
    Industry: Optional[str] = Field(None, description="Industry")
    Lead_Source: Optional[str] = Field(None, description="How the lead was acquired")
    Lead_Status: Optional[str] = Field(None, description="Current lead status")
    Website: Optional[str] = Field(None, description="Website URL")
    Description: Optional[str] = Field(None, description="Additional notes")
    
    # Address fields
    Street: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Zip_Code: Optional[str] = None
    Country: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""
    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead (all fields optional)."""
    
    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    Email: Optional[EmailStr] = None
    Phone: Optional[str] = None
    Mobile: Optional[str] = None
    Company: Optional[str] = None
    Title: Optional[str] = None
    Industry: Optional[str] = None
    Lead_Source: Optional[str] = None
    Lead_Status: Optional[str] = None
    Website: Optional[str] = None
    Description: Optional[str] = None
    Street: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Zip_Code: Optional[str] = None
    Country: Optional[str] = None


class LeadResponse(BaseModel):
    """Response schema for a single lead."""
    
    data: Dict[str, Any] = Field(..., description="Lead data from Zoho")
    
    class Config:
        extra = "allow"


class LeadListResponse(BaseModel):
    """Response schema for a list of leads."""
    
    data: List[Dict[str, Any]] = Field(default_factory=list, description="List of leads")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Records per page")
    total_count: int = Field(0, description="Total number of records in this response")
    more_records: bool = Field(False, description="Whether more records are available")
