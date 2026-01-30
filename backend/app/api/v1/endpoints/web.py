"""
Web scraping endpoints for fetching company data from URLs.

When a user searches for a URL and no matching leads are found,
these endpoints can be used to extract company information from the website.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from loguru import logger

from app.services.web.scraper import website_scraper

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
