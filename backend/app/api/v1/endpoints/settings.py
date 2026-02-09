"""
Settings endpoints for managing system configuration.

Allows viewing and updating LLM prompts at runtime for both
the Leads and Application (Deals) modules.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.services.llm.prompt_manager import prompt_manager

router = APIRouter()


class PromptsResponse(BaseModel):
    """Response containing all prompts from both modules."""
    # Lead prompts
    system_prompt: str
    analysis_prompt: str
    # Deal prompts
    deal_system_prompt: str
    deal_analysis_prompt: str
    deal_scoring_system_prompt: str
    deal_scoring_prompt: str


class PromptUpdateRequest(BaseModel):
    """Request to update prompts. All fields are optional - only provided fields are updated."""
    # Lead prompts
    system_prompt: Optional[str] = None
    analysis_prompt: Optional[str] = None
    # Deal prompts
    deal_system_prompt: Optional[str] = None
    deal_analysis_prompt: Optional[str] = None
    deal_scoring_system_prompt: Optional[str] = None
    deal_scoring_prompt: Optional[str] = None


class PromptUpdateResponse(BaseModel):
    """Response after updating prompts."""
    success: bool
    message: str
    # Lead prompts
    system_prompt: str
    analysis_prompt: str
    # Deal prompts
    deal_system_prompt: str
    deal_analysis_prompt: str
    deal_scoring_system_prompt: str
    deal_scoring_prompt: str


@router.get("/prompts", response_model=PromptsResponse)
async def get_prompts():
    """
    Get all current LLM prompts for both Leads and Application modules.
    """
    try:
        prompts = prompt_manager.get_all_prompts()
        return PromptsResponse(**prompts)
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts", response_model=PromptUpdateResponse)
async def update_prompts(request: PromptUpdateRequest):
    """
    Update LLM prompts for Leads and/or Application modules.
    
    You can update any combination of prompts. Only provided (non-null) fields
    are updated; others remain unchanged.
    
    Validation rules:
    - analysis_prompt must contain {lead_data} placeholder
    - deal_analysis_prompt must contain {deal_data} placeholder
    - deal_scoring_prompt must contain {deal_data} and {analysis_summary} placeholders
    """
    try:
        # Validate lead analysis prompt
        if request.analysis_prompt is not None:
            if "{lead_data}" not in request.analysis_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Lead analysis prompt must contain {lead_data} placeholder"
                )
        
        # Validate deal analysis prompt
        if request.deal_analysis_prompt is not None:
            if "{deal_data}" not in request.deal_analysis_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Deal analysis prompt must contain {deal_data} placeholder"
                )
        
        # Validate deal scoring prompt
        if request.deal_scoring_prompt is not None:
            if "{deal_data}" not in request.deal_scoring_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Deal scoring prompt must contain {deal_data} placeholder"
                )
            if "{analysis_summary}" not in request.deal_scoring_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Deal scoring prompt must contain {analysis_summary} placeholder"
                )
        
        # Build kwargs for update
        update_kwargs = {}
        if request.system_prompt is not None:
            update_kwargs["system_prompt"] = request.system_prompt
        if request.analysis_prompt is not None:
            update_kwargs["analysis_prompt"] = request.analysis_prompt
        if request.deal_system_prompt is not None:
            update_kwargs["deal_system_prompt"] = request.deal_system_prompt
        if request.deal_analysis_prompt is not None:
            update_kwargs["deal_analysis_prompt"] = request.deal_analysis_prompt
        if request.deal_scoring_system_prompt is not None:
            update_kwargs["deal_scoring_system_prompt"] = request.deal_scoring_system_prompt
        if request.deal_scoring_prompt is not None:
            update_kwargs["deal_scoring_prompt"] = request.deal_scoring_prompt
        
        if not update_kwargs:
            raise HTTPException(
                status_code=400,
                detail="No prompts provided to update"
            )
        
        success = prompt_manager.update_prompts(**update_kwargs)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save prompts"
            )
        
        # Sync updated prompts to deal analysis service
        _sync_deal_prompts()
        
        prompts = prompt_manager.get_all_prompts()
        
        logger.info(f"Prompts updated successfully (fields: {list(update_kwargs.keys())})")
        
        return PromptUpdateResponse(
            success=True,
            message="Prompts updated successfully",
            **prompts,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/reset", response_model=PromptUpdateResponse)
async def reset_prompts():
    """
    Reset all prompts to default values for both Leads and Application modules.
    """
    try:
        success = prompt_manager.reset_to_defaults()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset prompts"
            )
        
        # Sync reset prompts to deal analysis service
        _sync_deal_prompts()
        
        prompts = prompt_manager.get_all_prompts()
        
        logger.info("All prompts reset to defaults")
        
        return PromptUpdateResponse(
            success=True,
            message="All prompts reset to defaults",
            **prompts,
        )
        
    except Exception as e:
        logger.error(f"Error resetting prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _sync_deal_prompts():
    """Push current deal prompts from prompt_manager into the deal_analysis_service."""
    try:
        from app.services.llm.deal_analysis_service import deal_analysis_service
        deal_analysis_service.update_prompts(
            system_prompt=prompt_manager.get_deal_system_prompt(),
            analysis_prompt=prompt_manager.get_deal_analysis_prompt(),
        )
        deal_analysis_service._scoring_system_prompt = prompt_manager.get_deal_scoring_system_prompt()
        deal_analysis_service._scoring_prompt_template = prompt_manager.get_deal_scoring_prompt()
    except Exception as e:
        logger.warning(f"Could not sync deal prompts: {e}")
