"""
Settings endpoints for managing system configuration.

Allows viewing and updating LLM prompts at runtime.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.services.llm.prompt_manager import prompt_manager

router = APIRouter()


class PromptsResponse(BaseModel):
    """Response containing all prompts."""
    system_prompt: str
    analysis_prompt: str


class PromptUpdateRequest(BaseModel):
    """Request to update prompts."""
    system_prompt: Optional[str] = None
    analysis_prompt: Optional[str] = None


class PromptUpdateResponse(BaseModel):
    """Response after updating prompts."""
    success: bool
    message: str
    system_prompt: str
    analysis_prompt: str


@router.get("/prompts", response_model=PromptsResponse)
async def get_prompts():
    """
    Get the current LLM prompts.
    
    Returns both the system prompt and analysis prompt template.
    """
    try:
        prompts = prompt_manager.get_all_prompts()
        return PromptsResponse(
            system_prompt=prompts["system_prompt"],
            analysis_prompt=prompts["analysis_prompt"],
        )
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts", response_model=PromptUpdateResponse)
async def update_prompts(request: PromptUpdateRequest):
    """
    Update LLM prompts.
    
    You can update one or both prompts. Changes take effect immediately
    for all subsequent lead analyses.
    
    Note: The analysis_prompt must contain {lead_data} placeholder.
    """
    try:
        # Validate analysis prompt if provided
        if request.analysis_prompt is not None:
            if "{lead_data}" not in request.analysis_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Analysis prompt must contain {lead_data} placeholder"
                )
        
        success = prompt_manager.update_prompts(
            system_prompt=request.system_prompt,
            analysis_prompt=request.analysis_prompt,
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save prompts"
            )
        
        # Get updated prompts
        prompts = prompt_manager.get_all_prompts()
        
        logger.info("Prompts updated successfully")
        
        return PromptUpdateResponse(
            success=True,
            message="Prompts updated successfully",
            system_prompt=prompts["system_prompt"],
            analysis_prompt=prompts["analysis_prompt"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/reset", response_model=PromptUpdateResponse)
async def reset_prompts():
    """
    Reset prompts to default values.
    
    This will restore both the system prompt and analysis prompt
    to their original default values.
    """
    try:
        success = prompt_manager.reset_to_defaults()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset prompts"
            )
        
        prompts = prompt_manager.get_all_prompts()
        
        logger.info("Prompts reset to defaults")
        
        return PromptUpdateResponse(
            success=True,
            message="Prompts reset to defaults",
            system_prompt=prompts["system_prompt"],
            analysis_prompt=prompts["analysis_prompt"],
        )
        
    except Exception as e:
        logger.error(f"Error resetting prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
