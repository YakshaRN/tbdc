"""
Web scraping endpoints for fetching company data from URLs.

When a user searches for a URL and no matching leads are found,
these endpoints can be used to extract company information from the website.
"""
import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from app.services.web.scraper import website_scraper
from app.services.llm.bedrock_service import lead_analysis_service
from app.services.llm.similar_customers_service import similar_customers_service
from app.services.dynamodb.lead_cache import lead_analysis_cache
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
            # Use search_for_lead - same method as leads endpoint
            materials = marketing_vector_store.search_for_lead(
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


def _normalize_domain(url: str) -> str:
    """Extract and normalize domain from a URL for use as cache key."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    # Remove www. prefix for consistent keying
    domain = re.sub(r"^www\.", "", domain).lower().strip()
    return domain


@router.get("/evaluate", response_model=EnrichedLeadResponse)
async def evaluate_website(
    url: str = Query(..., description="The website URL to evaluate")
):
    """
    One-shot endpoint: scrape a website, run LLM analysis, and cache in DynamoDB.
    
    If the URL has been evaluated before, returns cached results immediately.
    Otherwise: scrapes → analyzes with LLM → caches → returns.
    
    The cache key is `web_{domain}` stored in the leads DynamoDB table.
    """
    logger.info(f"Evaluate website request: {url}")
    
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    domain = _normalize_domain(url)
    if not domain:
        raise HTTPException(status_code=400, detail="Could not extract domain from URL")
    
    cache_key = f"web_{domain}"
    logger.info(f"Website cache key: {cache_key} (domain: {domain})")
    
    # --- 1. Check DynamoDB cache ---
    try:
        cached = lead_analysis_cache.get_cached_data(cache_key)
        if cached:
            analysis, marketing_materials, similar_customers = cached
            logger.info(f"Cache HIT for website {domain}")
            # Reconstruct the lead-like data from the cached analysis
            lead_like_data = {
                "id": cache_key,
                "Company": analysis.company_name or domain,
                "Website": url,
                "Description": "",
                "Email": "",
                "Phone": "",
                "Country": "Unknown",
                "Lead_Source": "Website Search",
                "First_Name": "",
                "Last_Name": "",
                "_source": "website",
            }
            return EnrichedLeadResponse(
                data=lead_like_data,
                analysis=analysis,
                analysis_available=True,
                from_cache=True,
                marketing_materials=marketing_materials,
                similar_customers=similar_customers
            )
    except Exception as e:
        logger.warning(f"Cache lookup failed for {cache_key}: {e}")
    
    # --- 2. Scrape the website ---
    logger.info(f"Cache MISS for website {domain} — scraping...")
    scrape_result = await website_scraper.fetch_website_data(url)
    
    if not scrape_result.get("success"):
        error_msg = scrape_result.get("error", "Failed to fetch website data")
        logger.warning(f"Scrape failed for {url}: {error_msg}")
        raise HTTPException(status_code=422, detail=f"Could not fetch website: {error_msg}")
    
    # --- 3. Build lead-like data for LLM ---
    company_name = scrape_result.get("company_name") or scrape_result.get("domain") or domain
    description = scrape_result.get("description") or ""
    keywords = scrape_result.get("keywords") or []
    
    lead_like_data = {
        "id": cache_key,
        "Company": company_name,
        "Website": scrape_result.get("url", url),
        "Description": description,
        "Email": scrape_result.get("email") or "",
        "Phone": scrape_result.get("phone") or "",
        "Country": "Unknown",
        "Lead_Source": "Website Search",
        "First_Name": "",
        "Last_Name": "",
        "Title": scrape_result.get("title") or "",
        "_source": "website",
        "_logo_url": scrape_result.get("logo_url"),
    }
    
    if keywords:
        keywords_str = ", ".join(keywords)
        if lead_like_data["Description"]:
            lead_like_data["Description"] += f"\nKeywords: {keywords_str}"
        else:
            lead_like_data["Description"] = f"Keywords: {keywords_str}"
    
    if scrape_result.get("address"):
        lead_like_data["Street"] = scrape_result["address"]
    
    # --- 4. Scrape full page text for richer LLM context ---
    website_text = None
    try:
        website_text = await website_scraper.fetch_page_text(url)
        if website_text:
            logger.info(f"Scraped {len(website_text)} chars of page text for {domain}")
    except Exception as e:
        logger.warning(f"Could not scrape page text for {domain}: {e}")
    
    # --- 5. Run LLM analysis ---
    logger.info(f"Running LLM analysis for website {domain}...")
    try:
        analysis = lead_analysis_service.analyze_lead(
            lead_like_data,
            website_text=website_text,
        )
    except Exception as e:
        logger.error(f"LLM analysis failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")
    
    # --- 6. Find similar customers ---
    logger.info("Finding similar customers...")
    similar_customers_data: List[Dict[str, Any]] = []
    try:
        analysis_dict = analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict()
        similar_customers_data = similar_customers_service.find_similar_customers(
            lead_data=lead_like_data,
            analysis_data=analysis_dict
        )
    except Exception as e:
        logger.warning(f"Could not find similar customers: {e}")
    
    # --- 7. Find marketing materials ---
    logger.info("Finding marketing materials...")
    marketing_materials: List[Dict[str, Any]] = []
    try:
        materials = marketing_vector_store.search_for_lead(
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
    
    # --- 8. Cache in DynamoDB ---
    logger.info(f"Caching website evaluation for {domain}...")
    try:
        lead_analysis_cache.save_analysis(
            lead_id=cache_key,
            analysis=analysis,
            marketing_materials=marketing_materials,
            similar_customers=similar_customers_data
        )
        logger.info(f"Successfully cached website evaluation for {domain}")
    except Exception as e:
        logger.warning(f"Failed to cache website evaluation for {domain}: {e}")
    
    logger.info(f"Website evaluation completed: domain={domain}, fit_score={analysis.fit_score}")
    
    return EnrichedLeadResponse(
        data=lead_like_data,
        analysis=analysis,
        analysis_available=True,
        from_cache=False,
        marketing_materials=marketing_materials,
        similar_customers=similar_customers_data
    )
