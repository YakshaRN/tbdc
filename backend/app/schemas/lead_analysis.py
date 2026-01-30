"""
Lead Analysis schemas for LLM-generated insights.
Tailored for TBDC's Pivot program - evaluating startups for Canada market fit.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LeadAnalysis(BaseModel):
    """
    AI-generated analysis of a lead/company for TBDC Pivot program.
    Evaluates startup fit for Canada and North America market entry.
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
    
    # Canada fit assessment
    likely_icp_canada: str = Field(
        default="Unknown", 
        description="Most likely Canadian customer profile (e.g., SMBs, mid-market enterprises, regulated industries)"
    )
    fit_score: int = Field(
        default=5, 
        ge=1, 
        le=10, 
        description="Canada market fit score from 1-10"
    )
    fit_assessment: str = Field(
        default="", 
        description="Brief assessment of Canada fit and TBDC Pivot suitability"
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


class LeadWithAnalysis(BaseModel):
    """
    Lead data combined with AI analysis.
    """
    lead_data: Dict[str, Any] = Field(..., description="Raw lead data from Zoho")
    analysis: LeadAnalysis = Field(..., description="AI-generated analysis")
    
    class Config:
        extra = "allow"


class MarketingMaterialMatch(BaseModel):
    """
    A marketing material matched by semantic similarity.
    """
    material_id: str = Field(..., description="Material ID")
    title: str = Field(..., description="Material title")
    link: str = Field(..., description="Link to the material")
    industry: str = Field(default="", description="Target industry")
    business_topics: str = Field(default="", description="Business topics")
    similarity_score: float = Field(..., description="Similarity score (0-1)")


class SimilarCustomer(BaseModel):
    """
    A similar customer identified by LLM analysis.
    """
    name: str = Field(..., description="Company name")
    description: str = Field(default="", description="Brief description of the company")
    industry: str = Field(default="", description="Company's industry")
    website: str = Field(default="", description="Company website if known")
    why_similar: str = Field(default="", description="Why this company is a good customer match")


class EnrichedLeadResponse(BaseModel):
    """
    Response schema for enriched lead endpoint.
    """
    data: Dict[str, Any] = Field(..., description="Lead data from Zoho")
    analysis: LeadAnalysis = Field(..., description="AI-generated lead analysis")
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
