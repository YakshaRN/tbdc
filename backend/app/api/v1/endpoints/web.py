"""
Web scraping endpoints for fetching company data from URLs.

When a user searches for a URL and no matching leads are found,
these endpoints can be used to extract company information from the website.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.services.web.scraper import website_scraper
from app.services.llm.bedrock_service import lead_analysis_service
from app.services.llm.similar_customers_service import similar_customers_service
from app.schemas.lead_analysis import LeadAnalysis

router = APIRouter()


class WebsiteDataResponse(BaseModel):
    """Response model for scraped website data."""
    success: bool
    url: str
    original_url: Optional[str] = None
    error: Optional[str] = None
    company_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    keywords: list[str] = []
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    social_links: dict[str, str] = {}
    logo_url: Optional[str] = None


class UrlValidationResponse(BaseModel):
    """Response for URL validation."""
    is_valid: bool
    normalized_url: Optional[str] = None


@router.get("/fetch", response_model=WebsiteDataResponse)
async def fetch_website_data(
    url: str = Query(..., description="The URL to fetch data from")
):
    """
    Fetch and extract company information from a website URL.
    
    This endpoint scrapes the given URL and extracts:
    - Company name
    - Description
    - Contact information (email, phone)
    - Social media links
    - Logo URL
    - Keywords/industry hints
    
    Use this when:
    - User searches for a URL in the search bar
    - No matching leads are found
    - User wants to preview company data before creating a lead
    """
    logger.info(f"Fetching website data for: {url}")
    
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Fetch the data
    result = await website_scraper.fetch_website_data(url)
    
    if not result.get("success"):
        logger.warning(f"Failed to fetch {url}: {result.get('error')}")
    
    return WebsiteDataResponse(**result)


@router.get("/validate", response_model=UrlValidationResponse)
async def validate_url(
    url: str = Query(..., description="The URL to validate")
):
    """
    Check if a string is a valid URL.
    
    Returns whether the URL is valid and the normalized version.
    """
    is_valid = website_scraper.is_valid_url(url)
    normalized = website_scraper.normalize_url(url) if is_valid else None
    
    return UrlValidationResponse(
        is_valid=is_valid,
        normalized_url=normalized
    )


class SimilarCustomer(BaseModel):
    """Similar customer suggestion."""
    name: str
    description: str
    industry: str
    website: Optional[str] = None
    why_similar: str


class WebsiteAnalysisRequest(BaseModel):
    """Request model for website analysis."""
    url: str
    company_name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    keywords: List[str] = []


class WebsiteAnalysisResponse(BaseModel):
    """Response model for website analysis."""
    success: bool
    error: Optional[str] = None
    analysis: Optional[LeadAnalysis] = None
    similar_customers: List[SimilarCustomer] = []


@router.post("/analyze", response_model=WebsiteAnalysisResponse)
async def analyze_website(request: WebsiteAnalysisRequest):
    """
    Analyze a website/company using LLM for Canada market fit.
    
    This endpoint takes website data and runs the same LLM analysis
    that is used for Zoho leads, generating:
    - Company fit assessment
    - Industry vertical
    - Business model classification
    - Fit score (1-10)
    - Strategic questions
    - Similar customer suggestions
    
    Use this when:
    - User has fetched website data via /web/fetch
    - User wants to evaluate the company without creating a Zoho lead
    """
    logger.info(f"Analyzing website: {request.url}")
    
    try:
        # Format website data like lead data for the LLM
        lead_like_data = {
            "Company": request.company_name or request.domain,
            "Website": request.url,
            "Description": request.description,
            "Email": request.email,
            "Phone": request.phone,
            "Country": "Unknown",  # Website doesn't provide this
            "Lead_Source": "Website Search",
        }
        
        # Add keywords as part of description if available
        if request.keywords:
            keywords_str = ", ".join(request.keywords)
            if lead_like_data["Description"]:
                lead_like_data["Description"] += f"\nKeywords: {keywords_str}"
            else:
                lead_like_data["Description"] = f"Keywords: {keywords_str}"
        
        # Add address if available
        if request.address:
            lead_like_data["Street"] = request.address
        
        # Run LLM analysis
        logger.info("Running LLM analysis on website data...")
        analysis = lead_analysis_service.analyze_lead(lead_like_data)
        
        # Find similar customers
        logger.info("Finding similar customers...")
        # Convert analysis to dict for the service
        analysis_dict = analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict()
        similar_customers_data = similar_customers_service.find_similar_customers(
            lead_data=lead_like_data,
            analysis_data=analysis_dict
        )
        
        # Convert to response format
        similar_customers = [
            SimilarCustomer(
                name=sc.get("name", "Unknown"),
                description=sc.get("description", ""),
                industry=sc.get("industry", ""),
                website=sc.get("website"),
                why_similar=sc.get("why_similar", "")
            )
            for sc in similar_customers_data
        ]
        
        logger.info(f"Website analysis completed: fit_score={analysis.fit_score}")
        
        return WebsiteAnalysisResponse(
            success=True,
            analysis=analysis,
            similar_customers=similar_customers
        )
        
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        return WebsiteAnalysisResponse(
            success=False,
            error=str(e)
        )
