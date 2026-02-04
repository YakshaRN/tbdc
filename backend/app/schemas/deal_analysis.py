"""
Deal Analysis schemas for LLM-generated insights.
Tailored for TBDC's Application module - evaluating deals for Canada market fit.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RevenueCustomer(BaseModel):
    """Top revenue customer information."""
    name: str = Field(default="", description="Customer/company name")
    industry: str = Field(default="", description="Customer industry")
    revenue_contribution: str = Field(default="", description="Revenue contribution or significance")
    description: str = Field(default="", description="Brief description of the customer relationship")


class DealAnalysis(BaseModel):
    """
    AI-generated analysis of a deal/company for TBDC Application module.
    Evaluates deal fit for Canada and North America market entry.
    """
    # Company identification
    company_name: str = Field(default="Unknown", description="Company name or primary domain")
    
    # Location
    country: str = Field(default="Unknown", description="Country where the company is based")
    region: str = Field(default="Unknown", description="Geographic region (e.g., North America, Europe, APAC)")
    
    # Summary
    summary: str = Field(
        default="", 
        description="Summary about company and its potential"
    )
    
    # Product & Business
    product_description: str = Field(
        default="Unknown", 
        description="One-line description of what the product does and for whom"
    )
    vertical: str = Field(
        default="Unknown", 
        description="Industry vertical (e.g., Fintech - SME, Healthtech, SaaS, Logistics, Data/AI)"
    )
    business_model: str = Field(
        default="Unknown", 
        description="Business model type (e.g., B2B, B2C, B2B2C, Marketplace, Subscription, Services-led)"
    )
    motion: str = Field(
        default="Unknown", 
        description="Go-to-market motion (SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy)"
    )
    
    # Company maturity
    raise_stage: str = Field(
        default="Unknown", 
        description="Funding stage (Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown)"
    )
    company_size: str = Field(
        default="Unknown", 
        description="Company size category (Startup, SMB, Mid-Market, Enterprise, Unknown)"
    )
    
    # Revenue & Customers - Top 5 customers from Zoho
    revenue_top_5_customers: List[RevenueCustomer] = Field(
        default_factory=list,
        description="Top 5 revenue-generating customers"
    )
    
    # Scoring Rubric - Like current status
    scoring_rubric: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring rubric with criteria and scores"
    )
    fit_score: int = Field(
        default=5, 
        ge=1, 
        le=10, 
        description="Overall fit score from 1-10"
    )
    fit_assessment: str = Field(
        default="", 
        description="Brief assessment of fit and suitability"
    )
    
    # ICP Mapping
    icp_mapping: str = Field(
        default="Unknown", 
        description="Ideal Customer Profile mapping for Canada market"
    )
    likely_icp_canada: str = Field(
        default="Unknown", 
        description="Most likely Canadian customer profile (e.g., SMBs, mid-market enterprises, regulated industries)"
    )
    
    # Support Required - From Zoho
    support_required: str = Field(
        default="", 
        description="Support required from TBDC (from Zoho deal data)"
    )
    support_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended support actions based on analysis"
    )
    
    # Insights and questions
    key_insights: List[str] = Field(
        default_factory=list, 
        description="3-5 insights about product, GTM readiness, or Canada relevance"
    )
    questions_to_ask: List[str] = Field(
        default_factory=list, 
        description="5-7 strategic questions to validate Canada entry, ICP, differentiation, and GTM feasibility"
    )
    
    # Confidence and notes
    confidence_level: str = Field(
        default="Medium", 
        description="Confidence in the analysis (High, Medium, Low)"
    )
    notes: List[str] = Field(
        default_factory=list, 
        description="Important caveats (B2C focus, services-heavy, regulatory friction, unclear product, etc.)"
    )

    class Config:
        extra = "allow"


class DealWithAnalysis(BaseModel):
    """
    Deal data combined with AI analysis.
    """
    deal_data: Dict[str, Any] = Field(..., description="Raw deal data from Zoho")
    analysis: DealAnalysis = Field(..., description="AI-generated analysis")
    
    class Config:
        extra = "allow"


class EnrichedDealResponse(BaseModel):
    """
    Response schema for enriched deal endpoint.
    """
    data: Dict[str, Any] = Field(..., description="Deal data from Zoho")
    analysis: DealAnalysis = Field(..., description="AI-generated deal analysis")
    analysis_available: bool = Field(default=True, description="Whether analysis was successful")
    from_cache: bool = Field(default=False, description="Whether analysis was retrieved from cache")
    marketing_materials: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Relevant marketing materials matched by semantic similarity"
    )
    similar_customers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Similar customers identified by LLM analysis"
    )
    
    class Config:
        extra = "allow"
