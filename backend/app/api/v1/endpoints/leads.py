"""
Lead management endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Query, Path, HTTPException
from loguru import logger

from app.services.zoho.crm_service import zoho_crm_service
from app.services.llm.bedrock_service import lead_analysis_service, bedrock_service
from app.services.llm.similar_customers_service import similar_customers_service
from app.services.dynamodb.lead_cache import lead_analysis_cache
from app.services.vector.marketing_vector_store import marketing_vector_store
from app.services.document.extractor import document_extractor
from app.schemas.lead import (
    LeadResponse,
    LeadListResponse,
    LeadCreate,
    LeadUpdate,
)
from app.schemas.lead_analysis import EnrichedLeadResponse, LeadAnalysis

router = APIRouter()


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1, description="Page number (ignored when fetch_all=true)"),
    per_page: int = Query(50, ge=1, le=200, description="Records per page (ignored when fetch_all=true)"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of fields to retrieve"
    ),
    lead_source: Optional[str] = Query(
        "LinkedIn Ads",
        description="Filter by lead source (e.g., 'LinkedIn Ads', 'Website', 'Referral')"
    ),
    fetch_all: bool = Query(
        True,
        description="If true, fetches ALL matching records (ignores pagination). Default is true for lead_source filter."
    ),
):
    """
    Fetch leads from Zoho CRM.
    
    Returns list of leads with optional field selection, sorting, and filtering.
    
    By default, when filtering by lead_source (e.g., LinkedIn Ads), ALL matching leads 
    are fetched by paginating through all results. Set fetch_all=false to use pagination.
    """
    try:
        field_list = fields.split(",") if fields else None
        
        # If lead_source filter is provided
        if lead_source:
            criteria = f"(Lead_Source:equals:{lead_source})"
            
            if fetch_all:
                # Fetch ALL matching leads by paginating through all pages
                logger.info(f"Fetching ALL leads with source: {lead_source}")
                result = await zoho_crm_service.search_all_leads(
                    criteria=criteria,
                    fields=field_list,
                )
            else:
                # Use regular pagination
                result = await zoho_crm_service.search_leads(
                    criteria=criteria,
                    page=page,
                    per_page=per_page,
                    fields=field_list,
                )
        else:
            result = await zoho_crm_service.get_leads(
                page=page,
                per_page=per_page,
                fields=field_list,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        
        leads = result.get("data", [])
        info = result.get("info", {})
        
        return LeadListResponse(
            data=leads,
            page=info.get("page", page),
            per_page=info.get("per_page", per_page),
            total_count=info.get("count", len(leads)),
            more_records=info.get("more_records", False),
        )
        
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=EnrichedLeadResponse)
async def get_lead(
    lead_id: str = Path(..., description="Zoho Lead ID"),
    skip_analysis: bool = Query(False, description="Skip LLM analysis and return only lead data"),
    refresh_analysis: bool = Query(False, description="Force regenerate analysis (ignore cache)"),
):
    """
    Get a specific lead by ID with AI-powered Canada market fit analysis.
    
    This endpoint fetches lead data from Zoho CRM and uses AWS Bedrock (Claude)
    to evaluate the company for TBDC's Pivot program, generating insights including:
    
    - Company identification and product description
    - Country, region, and geographic context
    - Industry vertical and business model classification
    - Go-to-market motion analysis
    - Funding stage and company size
    - Canada ICP (Ideal Customer Profile) assessment
    - Fit score (1-10) for Canada market entry
    - Strategic questions to validate Canada GTM feasibility
    - Key insights and important caveats/notes
    
    Analysis is cached in DynamoDB. First request generates analysis via LLM,
    subsequent requests return cached data.
    
    Query Parameters:
    - skip_analysis=true: Return only lead data without any analysis
    - refresh_analysis=true: Force regenerate analysis (ignore cache)
    """
    try:
        # Step 1: Fetch lead data from Zoho
        result = await zoho_crm_service.get_lead_by_id(lead_id)
        
        if not result.get("data"):
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead_data = result["data"][0]
        
        # Step 2: Handle analysis
        marketing_materials = []
        similar_customers = []
        
        if skip_analysis:
            # Return default analysis if explicitly skipped
            analysis = LeadAnalysis(
                company_name=lead_data.get("Company", "Unknown"),
                country=lead_data.get("Country", "Unknown"),
                region="Unknown",
                product_description="Analysis skipped",
                vertical=lead_data.get("Industry", "Unknown"),
                business_model="Unknown",
                motion="Unknown",
                raise_stage="Unknown",
                company_size="Unknown",
                likely_icp_canada="Unknown",
                fit_score=5,
                fit_assessment="Analysis was explicitly skipped",
                key_insights=[],
                questions_to_ask=[],
                confidence_level="Low",
                notes=["Analysis was skipped by user request"],
            )
            analysis_available = False
            from_cache = False
        elif not bedrock_service.is_configured:
            # Bedrock not configured
            logger.warning("AWS Bedrock not configured, returning default analysis")
            analysis = LeadAnalysis(
                company_name=lead_data.get("Company", "Unknown"),
                country=lead_data.get("Country", "Unknown"),
                region="Unknown",
                product_description="Unable to analyze - LLM not configured",
                vertical=lead_data.get("Industry", "Unknown"),
                business_model="Unknown",
                motion="Unknown",
                raise_stage="Unknown",
                company_size="Unknown",
                likely_icp_canada="Unknown",
                fit_score=5,
                fit_assessment="Analysis not available - AWS Bedrock not configured",
                key_insights=[],
                questions_to_ask=[
                    "What is your core product and who is your primary customer?",
                    "Have you explored the Canadian market before?",
                    "What is your current GTM motion?",
                    "What stage of funding are you at?",
                    "What would success in Canada look like for you?",
                ],
                confidence_level="Low",
                notes=["AWS Bedrock LLM not configured"],
            )
            analysis_available = False
            from_cache = False
        else:
            # Step 2a: Check DynamoDB cache first (unless refresh requested)
            cached_data = None
            
            if not refresh_analysis and lead_analysis_cache.is_enabled:
                cached_data = lead_analysis_cache.get_cached_data(lead_id)
            
            if cached_data:
                # Use cached analysis, marketing materials, and similar customers
                analysis, marketing_materials, similar_customers = cached_data
                logger.info(f"Using cached data for lead {lead_id}: {len(marketing_materials)} materials, {len(similar_customers)} similar customers")
                analysis_available = True
                from_cache = True
            else:
                # Step 2b: Fetch and extract text from attachments (pitch decks, PDFs, etc.)
                attachment_text = ""
                try:
                    logger.info(f"Fetching attachments for lead {lead_id}...")
                    attachments = await zoho_crm_service.get_lead_attachments_with_content(lead_id)
                    
                    if attachments:
                        logger.info(f"Found {len(attachments)} attachments for lead {lead_id}")
                        
                        # Extract text from documents
                        extractions = document_extractor.extract_from_attachments(attachments)
                        
                        if extractions:
                            attachment_text = document_extractor.combine_extracted_text(extractions)
                            logger.info(f"Extracted {len(attachment_text)} chars from {len(extractions)} documents")
                    else:
                        logger.debug(f"No attachments found for lead {lead_id}")
                        
                except Exception as e:
                    logger.warning(f"Error fetching/extracting attachments: {e}")
                
                # Step 2c: Generate new analysis using Bedrock LLM (including attachment content)
                logger.info(f"Generating LLM analysis for lead {lead_id}")
                analysis = lead_analysis_service.analyze_lead(
                    lead_data=lead_data,
                    attachment_text=attachment_text if attachment_text else None
                )
                analysis_available = True
                from_cache = False
                
                # Step 2d: Get relevant marketing materials (if indexed)
                if marketing_vector_store.is_indexed:
                    try:
                        marketing_materials = marketing_vector_store.search_for_lead(lead_data, top_k=5)
                        logger.info(f"Found {len(marketing_materials)} relevant marketing materials for lead {lead_id}")
                    except Exception as e:
                        logger.warning(f"Error fetching marketing materials: {e}")
                        marketing_materials = []
                
                # Step 2e: Find similar customers using LLM
                try:
                    # Convert analysis to dict for context
                    analysis_dict = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis.dict()
                    similar_customers = similar_customers_service.find_similar_customers(
                        lead_data=lead_data,
                        analysis_data=analysis_dict
                    )
                    logger.info(f"Found {len(similar_customers)} similar customers for lead {lead_id}")
                except Exception as e:
                    logger.warning(f"Error finding similar customers: {e}")
                    similar_customers = []
                
                # Step 2f: Cache everything in DynamoDB
                if lead_analysis_cache.is_enabled:
                    lead_analysis_cache.save_analysis(
                        lead_id, 
                        analysis, 
                        marketing_materials,
                        similar_customers
                    )
        
        return EnrichedLeadResponse(
            data=lead_data,
            analysis=analysis,
            analysis_available=analysis_available,
            from_cache=from_cache,
            marketing_materials=marketing_materials,
            similar_customers=similar_customers,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=LeadResponse)
async def create_lead(lead: LeadCreate):
    """
    Create a new lead in Zoho CRM.
    """
    try:
        result = await zoho_crm_service.create_lead(lead.model_dump(exclude_none=True))
        
        if result.get("data"):
            return LeadResponse(data=result["data"][0])
        
        raise HTTPException(status_code=400, detail="Failed to create lead")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str = Path(..., description="Zoho Lead ID"),
    lead: LeadUpdate = ...,
):
    """
    Update an existing lead.
    """
    try:
        result = await zoho_crm_service.update_lead(
            lead_id,
            lead.model_dump(exclude_none=True)
        )
        
        if result.get("data"):
            return LeadResponse(data=result["data"][0])
        
        raise HTTPException(status_code=400, detail="Failed to update lead")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str = Path(..., description="Zoho Lead ID"),
):
    """
    Delete a lead.
    """
    try:
        await zoho_crm_service.delete_lead(lead_id)
        return {"message": "Lead deleted successfully", "id": lead_id}
        
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/")
async def search_leads(
    email: Optional[str] = Query(None, description="Search by email"),
    phone: Optional[str] = Query(None, description="Search by phone"),
    company: Optional[str] = Query(None, description="Search by company"),
    criteria: Optional[str] = Query(
        None,
        description="Custom Zoho search criteria"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """
    Search leads with various criteria.
    
    You can use predefined search params (email, phone, company) or
    provide a custom Zoho criteria string.
    
    Example criteria: "(Email:equals:test@example.com)"
    """
    try:
        # Build criteria from params
        if criteria:
            search_criteria = criteria
        else:
            conditions = []
            if email:
                conditions.append(f"(Email:equals:{email})")
            if phone:
                conditions.append(f"(Phone:equals:{phone})")
            if company:
                conditions.append(f"(Company:contains:{company})")
            
            if not conditions:
                raise HTTPException(
                    status_code=400,
                    detail="At least one search parameter is required"
                )
            
            search_criteria = "and".join(conditions) if len(conditions) > 1 else conditions[0]
        
        result = await zoho_crm_service.search_leads(
            criteria=search_criteria,
            page=page,
            per_page=per_page,
        )
        
        return {
            "data": result.get("data", []),
            "info": result.get("info", {}),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
