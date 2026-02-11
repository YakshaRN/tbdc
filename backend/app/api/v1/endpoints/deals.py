"""
Deal management endpoints for the Application module.
"""
from typing import Optional, List
from fastapi import APIRouter, Query, Path, HTTPException
from loguru import logger

from app.services.zoho.crm_service import zoho_crm_service
from app.services.llm.bedrock_service import bedrock_service
from app.services.llm.deal_analysis_service import deal_analysis_service
from app.services.llm.similar_customers_service import similar_customers_service
from app.services.dynamodb.deal_cache import deal_analysis_cache
from app.services.vector.marketing_vector_store import marketing_vector_store
from app.services.document.extractor import document_extractor
from app.schemas.deal import (
    DealResponse,
    DealListResponse,
    DealCreate,
    DealUpdate,
)
from app.schemas.deal_analysis import EnrichedDealResponse, DealAnalysis

router = APIRouter()


@router.get("/", response_model=DealListResponse)
async def list_deals(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=200, description="Records per page (default 100)"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of fields to retrieve"
    ),
    stage: Optional[str] = Query(
        None,
        description="Filter by deal stage (e.g., 'Qualification', 'Proposal')"
    ),
    fetch_all: bool = Query(
        False,
        description="If true, fetches ALL matching records (ignores pagination). Default is false to use pagination."
    ),
):
    """
    Fetch deals from Zoho CRM.
    
    Returns list of deals with optional field selection, sorting, and filtering.
    """
    try:
        field_list = fields.split(",") if fields else None
        
        # If stage filter is provided
        if stage:
            criteria = f"(Stage:equals:{stage})"
            
            if fetch_all:
                # Fetch ALL matching deals by paginating through all pages
                logger.info(f"Fetching ALL deals with stage: {stage}")
                result = await zoho_crm_service.search_all_deals(
                    criteria=criteria,
                    fields=field_list,
                )
            else:
                # Use regular pagination
                result = await zoho_crm_service.search_deals(
                    criteria=criteria,
                    page=page,
                    per_page=per_page,
                    fields=field_list,
                )
        else:
            result = await zoho_crm_service.get_deals(
                page=page,
                per_page=per_page,
                fields=field_list,
            )
        
        deals = result.get("data", [])
        info = result.get("info", {})
        
        return DealListResponse(
            data=deals,
            page=info.get("page", page),
            per_page=info.get("per_page", per_page),
            total_count=info.get("count", len(deals)),
            more_records=info.get("more_records", False),
        )
        
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{deal_id}", response_model=EnrichedDealResponse)
async def get_deal(
    deal_id: str = Path(..., description="Zoho Deal ID"),
    skip_analysis: bool = Query(False, description="Skip LLM analysis and return only deal data"),
    refresh_analysis: bool = Query(False, description="Force regenerate analysis (ignore cache)"),
):
    """
    Get a specific deal by ID with AI-powered Canada market fit analysis.
    
    This endpoint fetches deal data from Zoho CRM and uses AWS Bedrock (Claude)
    to evaluate the company for TBDC's Application program, generating insights including:
    
    - Company identification and product description
    - Country, region, and geographic context
    - Industry vertical and business model classification
    - Go-to-market motion analysis
    - Revenue from Top 5 Customers
    - Scoring Rubric and Fit Score
    - ICP Mapping for Canada market
    - Support Required from TBDC
    - Strategic questions to validate Canada GTM feasibility
    
    Analysis is cached in DynamoDB. First request generates analysis via LLM,
    subsequent requests return cached data.
    
    Query Parameters:
    - skip_analysis=true: Return only deal data without any analysis
    - refresh_analysis=true: Force regenerate analysis (ignore cache)
    """
    try:
        # Step 1: Fetch deal data from Zoho
        result = await zoho_crm_service.get_deal_by_id(deal_id)
        
        if not result.get("data"):
            raise HTTPException(status_code=404, detail="Deal not found")
        
        deal_data = result["data"][0]
        
        # Step 2: Handle analysis
        marketing_materials = []
        similar_customers = []
        
        if skip_analysis:
            # Return default analysis if explicitly skipped
            analysis = DealAnalysis(
                company_name=deal_data.get("Deal_Name") or "Unknown",
                country="Unknown",
                region="Unknown",
                product_description="Analysis skipped",
                vertical="Unknown",
                business_model="Unknown",
                motion="Unknown",
                raise_stage="Unknown",
                company_size="Unknown",
                likely_icp_canada="Unknown",
                icp_mapping="Unknown",
                fit_score=5,
                fit_assessment="Analysis was explicitly skipped",
                support_required=deal_data.get("Support_Required", ""),
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
            analysis = DealAnalysis(
                company_name=deal_data.get("Deal_Name") or "Unknown",
                country="Unknown",
                region="Unknown",
                product_description="Unable to analyze - LLM not configured",
                vertical="Unknown",
                business_model="Unknown",
                motion="Unknown",
                raise_stage="Unknown",
                company_size="Unknown",
                likely_icp_canada="Unknown",
                icp_mapping="Unknown",
                fit_score=5,
                fit_assessment="Analysis not available - AWS Bedrock not configured",
                support_required=deal_data.get("Support_Required", ""),
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
            
            if not refresh_analysis and deal_analysis_cache.is_enabled:
                cached_data = deal_analysis_cache.get_cached_data(deal_id)
            
            if cached_data:
                # Use cached analysis, marketing materials, and similar customers
                analysis, marketing_materials, similar_customers = cached_data
                logger.info(f"Using cached data for deal {deal_id}: {len(marketing_materials)} materials, {len(similar_customers)} similar customers")
                analysis_available = True
                from_cache = True
            else:
                # Step 2b: Fetch and extract text from attachments (pitch decks, PDFs, etc.)
                attachment_text = ""
                try:
                    logger.info(f"Fetching attachments for deal {deal_id}...")
                    attachments = await zoho_crm_service.get_deal_attachments_with_content(deal_id)
                    
                    if attachments:
                        logger.info(f"Found {len(attachments)} attachments for deal {deal_id}")
                        
                        # Extract text from documents
                        extractions = document_extractor.extract_from_attachments(attachments)
                        
                        if extractions:
                            attachment_text = document_extractor.combine_extracted_text(extractions)
                            logger.info(f"Extracted {len(attachment_text)} chars from {len(extractions)} documents")
                    else:
                        logger.debug(f"No attachments found for deal {deal_id}")
                        
                except Exception as e:
                    logger.warning(f"Error fetching/extracting deal attachments: {e}")
                
                # Step 2c: Generate new analysis using Deal Analysis Service directly
                # Use the dedicated deal analysis service with deal-specific prompts
                logger.info(f"Generating LLM analysis for deal {deal_id}")
                analysis = deal_analysis_service.analyze_deal(
                    deal_data=deal_data,
                    attachment_text=attachment_text if attachment_text else None
                )
                
                # Add support_required from Zoho if not already set
                if not analysis.support_required and deal_data.get("Support_Required"):
                    analysis.support_required = deal_data.get("Support_Required", "")
                
                analysis_available = True
                from_cache = False
                
                # Step 2d: Get relevant marketing materials (if indexed)
                # Create a minimal data dict for marketing material search
                search_data = {
                    "Company": deal_data.get("Deal_Name"),
                    "Industry": deal_data.get("Industry") or analysis.vertical,
                    "Description": deal_data.get("Description") or analysis.product_description,
                }
                
                if marketing_vector_store.is_indexed:
                    try:
                        marketing_materials = marketing_vector_store.search_for_lead(search_data, top_k=5)
                        logger.info(f"Found {len(marketing_materials)} relevant marketing materials for deal {deal_id}")
                    except Exception as e:
                        logger.warning(f"Error fetching marketing materials: {e}")
                        marketing_materials = []
                
                # Step 2e: Find similar customers using LLM
                try:
                    # Convert analysis to dict for context
                    analysis_dict = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis.dict()
                    similar_customers = similar_customers_service.find_similar_customers(
                        lead_data=search_data,
                        analysis_data=analysis_dict
                    )
                    logger.info(f"Found {len(similar_customers)} similar customers for deal {deal_id}")
                except Exception as e:
                    logger.warning(f"Error finding similar customers: {e}")
                    similar_customers = []
                
                # Step 2f: Cache everything in DynamoDB
                if deal_analysis_cache.is_enabled:
                    deal_analysis_cache.save_analysis(
                        deal_id, 
                        analysis, 
                        marketing_materials,
                        similar_customers
                    )
        
        return EnrichedDealResponse(
            data=deal_data,
            analysis=analysis,
            analysis_available=analysis_available,
            from_cache=from_cache,
            marketing_materials=marketing_materials,
            similar_customers=similar_customers,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DealResponse)
async def create_deal(deal: DealCreate):
    """
    Create a new deal in Zoho CRM.
    """
    try:
        result = await zoho_crm_service.create_deal(deal.model_dump(exclude_none=True))
        
        if result.get("data"):
            return DealResponse(data=result["data"][0])
        
        raise HTTPException(status_code=400, detail="Failed to create deal")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str = Path(..., description="Zoho Deal ID"),
    deal: DealUpdate = ...,
):
    """
    Update an existing deal.
    """
    try:
        result = await zoho_crm_service.update_deal(
            deal_id,
            deal.model_dump(exclude_none=True)
        )
        
        if result.get("data"):
            return DealResponse(data=result["data"][0])
        
        raise HTTPException(status_code=400, detail="Failed to update deal")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str = Path(..., description="Zoho Deal ID"),
):
    """
    Delete a deal.
    """
    try:
        await zoho_crm_service.delete_deal(deal_id)
        return {"message": "Deal deleted successfully", "id": deal_id}
        
    except Exception as e:
        logger.error(f"Error deleting deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/search/")
# async def search_deals(
#     deal_name: Optional[str] = Query(None, description="Search by deal name"),
#     account_name: Optional[str] = Query(None, description="Search by account name"),
#     stage: Optional[str] = Query(None, description="Search by stage"),
#     criteria: Optional[str] = Query(
#         None,
#         description="Custom Zoho search criteria"
#     ),
#     page: int = Query(1, ge=1),
#     per_page: int = Query(50, ge=1, le=200),
# ):

#     """
#     Search deals with various criteria.
    
#     You can use predefined search params (deal_name, account_name, stage) or
#     provide a custom Zoho criteria string.
    
#     Example criteria: "(Stage:equals:Qualification)"
#     """
#     try:
#         # Build criteria from params
#         if criteria:
#             search_criteria = criteria
#         else:
#             conditions = []
#             if deal_name:
#                 conditions.append(f"(Deal_Name:contains:{deal_name})")
#             if account_name:
#                 conditions.append(f"(Account_Name:contains:{account_name})")
#             if stage:
#                 conditions.append(f"(Stage:equals:{stage})")
            
#             if not conditions:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="At least one search parameter is required"
#                 )
            
#             search_criteria = "and".join(conditions) if len(conditions) > 1 else conditions[0]
        
#         result = await zoho_crm_service.search_deals(
#             criteria=search_criteria,
#             page=page,
#             per_page=per_page,
#         )
        
#         return {
#             "data": result.get("data", []),
#             "info": result.get("info", {}),
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error searching deals: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/")
async def search_deals(
    search_query: Optional[str] = Query(
        None, 
        description="Search across deal name, account name, and contact name"
    ),
    deal_name: Optional[str] = Query(None, description="Search by deal name"),
    account_name: Optional[str] = Query(None, description="Search by account name"),
    contact_name: Optional[str] = Query(None, description="Search by contact name"),
    stage: Optional[str] = Query(None, description="Search by stage"),
    criteria: Optional[str] = Query(
        None,
        description="Custom Zoho search criteria"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """
    Search deals with various criteria.
    
    - Use search_query for broad search across deal name, account name, and contact name
    - Use specific params (deal_name, account_name, stage) for targeted search
    - Or provide custom Zoho criteria string
    
    Example: /search/?search_query=Acme
    """
    try:
        # Build criteria from params
        if criteria:
            search_criteria = criteria
        elif search_query:
            # Search across multiple fields using OR
            conditions = [
                f"(Deal_Name:starts_with:{search_query})",
                f"(Account_Name:starts_with:{search_query})",
                f"(Contact_Name:starts_with:{search_query})",
                f"(Owner.name:equals:{search_query})"
            ]
            # Proper OR formatting: (((condition1)or(condition2)or(condition3)))
            search_criteria = "((" + ")or(".join(conditions) + "))"
            
        else:
            # Individual field searches
            conditions = []
            if deal_name:
                conditions.append(f"(Deal_Name:starts_with:{deal_name})")
            if account_name:
                conditions.append(f"(Account_Name:starts_with:{account_name})")
            if contact_name:
                conditions.append(f"(Contact_Name:starts_with:{contact_name})")
            if stage:
                conditions.append(f"(Stage:equals:{stage})")
            
            if not conditions:
                raise HTTPException(
                    status_code=400,
                    detail="At least one search parameter is required"
                )
            
            # Properly format multiple conditions with AND
            if len(conditions) > 1:
                search_criteria = "((" + ")and(".join(conditions) + "))"
            else:
                search_criteria = conditions[0]
        
        logger.info(f"Search criteria: {search_criteria}")
        result = await zoho_crm_service.search_deals(
            criteria=search_criteria,
            page=page,
            per_page=per_page,
        )
        data = result.get("data", [])
        info = result.get("info", {})
        # Ensure pagination info for frontend (Zoho returns page, per_page, count, more_records)
        info.setdefault("page", page)
        info.setdefault("per_page", per_page)
        info.setdefault("more_records", False)
        return {
            "data": data,
            "info": info,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))