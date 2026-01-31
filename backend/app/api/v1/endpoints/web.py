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
from app.services.vector.marketing_vector_store import marketing_vector_store
from app.schemas.lead_analysis import LeadAnalysis, EnrichedLeadResponse

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


class WebsiteAnalysisRequest(BaseModel):
    """Request model for website analysis."""
    url: str
    company_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    keywords: List[str] = []
    logo_url: Optional[str] = None


@router.post("/analyze", response_model=EnrichedLeadResponse)
async def analyze_website(request: WebsiteAnalysisRequest):
    """
    Analyze a website/company using LLM for Canada market fit.
    
    Returns the SAME format as /leads/{id} endpoint (EnrichedLeadResponse)
    so the frontend can use the same UI component for both.
    
    This endpoint takes website data and runs the same LLM analysis
    that is used for Zoho leads, generating:
    - Company fit assessment
    - Industry vertical
    - Business model classification
    - Fit score (1-10)
    - Strategic questions
    - Similar customer suggestions
    - Marketing materials
    """
    logger.info(f"Analyzing website: {request.url}")
    
    try:
        # Create lead-like data structure from website data
        # This mimics Zoho lead data format so we can use the same LLM prompts
        lead_like_data = {
            "id": f"website_{request.domain or 'unknown'}",
            "Company": request.company_name or request.domain,
            "Website": request.url,
            "Description": request.description,
            "Email": request.email,
            "Phone": request.phone,
            "Country": "Unknown",
            "Lead_Source": "Website Search",
            "First_Name": "",
            "Last_Name": "",
            "Title": request.title,
            # Add a flag to identify this as website data
            "_source": "website",
            "_logo_url": request.logo_url,
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
        
        # Run LLM analysis (same as Zoho leads)
        logger.info("Running LLM analysis on website data...")
        analysis = lead_analysis_service.analyze_lead(lead_like_data)
        
        # Find similar customers (same as Zoho leads)
        logger.info("Finding similar customers...")
        analysis_dict = analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict()
        similar_customers_data = similar_customers_service.find_similar_customers(
            lead_data=lead_like_data,
            analysis_data=analysis_dict
        )
        
        # Find relevant marketing materials (same as Zoho leads)
        logger.info("Finding relevant marketing materials...")
        marketing_materials = []
        try:
            materials = marketing_vector_store.find_relevant_materials(
                analysis=analysis,
                lead_data=lead_like_data,
                top_k=5
            )
            marketing_materials = [
                {
                    "material_id": m.get("material_id", ""),
                    "title": m.get("title", ""),
                    "link": m.get("link", ""),
                    "industry": m.get("industry", ""),
                    "business_topics": m.get("business_topics", ""),
                    "similarity_score": m.get("similarity_score", 0.0),
                }
                for m in materials
            ]
            logger.info(f"Found {len(marketing_materials)} relevant marketing materials")
        except Exception as e:
            logger.warning(f"Could not fetch marketing materials: {e}")
        
        logger.info(f"Website analysis completed: fit_score={analysis.fit_score}")
        
        # Return same format as EnrichedLeadResponse
        return EnrichedLeadResponse(
            data=lead_like_data,
            analysis=analysis,
            analysis_available=True,
            from_cache=False,
            marketing_materials=marketing_materials,
            similar_customers=similar_customers_data
        )
        
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        # Return error in same format
        from app.schemas.lead_analysis import LeadAnalysis as LA
        return EnrichedLeadResponse(
            data={"Company": request.company_name or request.domain, "Website": request.url, "error": str(e)},
            analysis=LA(company_name=request.company_name or "Unknown"),
            analysis_available=False,
            from_cache=False,
            marketing_materials=[],
            similar_customers=[]
        )
