"""
Generic Zoho CRM endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query, Path
from loguru import logger

from app.services.zoho.crm_service import zoho_crm_service

router = APIRouter()


@router.get("/modules/{module}")
async def get_module_records(
    module: str = Path(..., description="Zoho module name (e.g., Leads, Contacts, Deals)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Records per page"),
    fields: Optional[str] = Query(None, description="Comma-separated fields"),
):
    """
    Fetch records from any Zoho CRM module.
    
    Supported modules: Leads, Contacts, Accounts, Deals, Tasks, Events, etc.
    """
    field_list = fields.split(",") if fields else None
    
    result = await zoho_crm_service.get_records(
        module=module,
        page=page,
        per_page=per_page,
        fields=field_list,
    )
    
    return {
        "module": module,
        "data": result.get("data", []),
        "info": result.get("info", {}),
    }


@router.get("/contacts/")
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    fields: Optional[str] = Query(None),
):
    """Fetch contacts from Zoho CRM."""
    field_list = fields.split(",") if fields else None
    result = await zoho_crm_service.get_contacts(
        page=page,
        per_page=per_page,
        fields=field_list,
    )
    return result


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str = Path(...)):
    """Get a specific contact by ID."""
    result = await zoho_crm_service.get_contact_by_id(contact_id)
    return result


@router.get("/deals/")
async def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    fields: Optional[str] = Query(None),
):
    """Fetch deals from Zoho CRM."""
    field_list = fields.split(",") if fields else None
    result = await zoho_crm_service.get_deals(
        page=page,
        per_page=per_page,
        fields=field_list,
    )
    return result


@router.get("/deals/{deal_id}")
async def get_deal(deal_id: str = Path(...)):
    """Get a specific deal by ID."""
    result = await zoho_crm_service.get_deal_by_id(deal_id)
    return result
