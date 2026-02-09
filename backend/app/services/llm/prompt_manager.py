"""
Prompt Manager Service.

Manages all LLM prompts (Leads and Deals/Application modules)
with persistence to a JSON file.
Allows runtime updates without restarting the server.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from app.core.config import settings


# ============================================================
# Lead Module Default Prompts
# ============================================================

DEFAULT_SYSTEM_PROMPT = """You are an expert B2B lead qualification specialist.

Your role is to evaluate global startups for Canada and/or North America fit.
You assess the company's product, business model, GTM motion, funding maturity, and suitability
for entering the Canadian market.

## Output Purpose
Your output is used by strategy and sales teams to:
- Decide whether the company is worth outreach
- Prioritize leads for programs
- Identify key Canada-specific GTM considerations

## Evaluation Rules
- Always review the company's official website first (homepage, product, solutions, or industries pages).
- Use 2-3 max third-party sources to cross-check information/reviews about the company.
- If the website is vague or unclear, you must explicitly state this and lower your confidence.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.
- Never invent product features or use cases.

## Response Format
Always respond with valid JSON only using this exact structure:

{
  "company_name": "Company name or primary domain",
  "country": "Country where the company is based",
  "region": "Geographic region (e.g., North America, Europe, APAC)",
  "summary": "Summary about company and its potential",
  "product_description": "One-line description or 'Unclear from site'",
  "vertical": "Industry vertical (e.g., Fintech, Healthtech, SaaS)",
  "business_model": "B2B, B2C, B2B2C, Marketplace, Subscription, Services-led",
  "motion": "SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy",
  "raise_stage": "Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown",
  "company_size": "Startup, SMB, Mid-Market, Enterprise, Unknown",
  "likely_icp_canada": "Most likely Canadian customer profile",
  "fit_score": 1-10,
  "fit_assessment": "Brief assessment of Canada fit",
  "key_insights": ["3-5 concise insights"],
  "questions_to_ask": ["5-7 strategic questions"],
  "confidence_level": "High, Medium, or Low",
  "notes": ["Important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product, or strong incumbents in Canada"]
}

Do not include explanations, markdown, or any text outside the JSON object."""

DEFAULT_ANALYSIS_PROMPT = """Evaluate the following company for Canada fit.

Company Input:
{lead_data}"""


# ============================================================
# All prompt keys and their defaults (loaded lazily from deal module)
# ============================================================

# Keys used for storage
LEAD_SYSTEM_PROMPT_KEY = "system_prompt"
LEAD_ANALYSIS_PROMPT_KEY = "analysis_prompt"
DEAL_SYSTEM_PROMPT_KEY = "deal_system_prompt"
DEAL_ANALYSIS_PROMPT_KEY = "deal_analysis_prompt"
DEAL_SCORING_SYSTEM_PROMPT_KEY = "deal_scoring_system_prompt"
DEAL_SCORING_PROMPT_KEY = "deal_scoring_prompt"


def _get_deal_defaults() -> Dict[str, str]:
    """
    Lazily import deal prompt defaults to avoid circular imports.
    The deal_analysis_service defines its own default prompts.
    """
    from app.services.llm.deal_analysis_service import (
        DEFAULT_DEAL_SYSTEM_PROMPT,
        DEFAULT_DEAL_ANALYSIS_PROMPT,
        SCORING_RUBRIC_SYSTEM_PROMPT,
        SCORING_RUBRIC_PROMPT,
    )
    return {
        DEAL_SYSTEM_PROMPT_KEY: DEFAULT_DEAL_SYSTEM_PROMPT,
        DEAL_ANALYSIS_PROMPT_KEY: DEFAULT_DEAL_ANALYSIS_PROMPT,
        DEAL_SCORING_SYSTEM_PROMPT_KEY: SCORING_RUBRIC_SYSTEM_PROMPT,
        DEAL_SCORING_PROMPT_KEY: SCORING_RUBRIC_PROMPT,
    }


class PromptManager:
    """
    Manages all LLM prompts (Leads + Deals) with file-based persistence.
    
    Stores prompts in a JSON file that persists across restarts.
    Provides methods to get and update prompts at runtime.
    """
    
    def __init__(self):
        self._prompts_file = settings.BASE_DIR / "data" / "prompts.json"
        self._prompts: Dict[str, str] = {}
        self._loaded = False
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        data_dir = self._prompts_file.parent
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_all_defaults(self) -> Dict[str, str]:
        """Get all default prompts (leads + deals)."""
        defaults = {
            LEAD_SYSTEM_PROMPT_KEY: DEFAULT_SYSTEM_PROMPT,
            LEAD_ANALYSIS_PROMPT_KEY: DEFAULT_ANALYSIS_PROMPT,
        }
        try:
            defaults.update(_get_deal_defaults())
        except Exception as e:
            logger.warning(f"Could not load deal prompt defaults: {e}")
        return defaults
    
    def _load_prompts(self) -> None:
        """Load prompts from file or use defaults."""
        if self._loaded:
            return
        
        self._ensure_data_dir()
        
        if self._prompts_file.exists():
            try:
                with open(self._prompts_file, "r", encoding="utf-8") as f:
                    self._prompts = json.load(f)
                logger.info(f"Loaded prompts from {self._prompts_file}")
            except Exception as e:
                logger.error(f"Error loading prompts: {e}")
                self._prompts = {}
        
        # Ensure all defaults are set (fills missing keys)
        defaults = self._get_all_defaults()
        for key, default_value in defaults.items():
            if key not in self._prompts:
                self._prompts[key] = default_value
        
        self._loaded = True
    
    def _save_prompts(self) -> bool:
        """Save prompts to file."""
        self._ensure_data_dir()
        
        try:
            with open(self._prompts_file, "w", encoding="utf-8") as f:
                json.dump(self._prompts, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved prompts to {self._prompts_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            return False
    
    # ----- Lead prompts -----
    
    def get_system_prompt(self) -> str:
        """Get the current lead system prompt."""
        self._load_prompts()
        return self._prompts.get(LEAD_SYSTEM_PROMPT_KEY, DEFAULT_SYSTEM_PROMPT)
    
    def get_analysis_prompt(self) -> str:
        """Get the current lead analysis prompt template."""
        self._load_prompts()
        return self._prompts.get(LEAD_ANALYSIS_PROMPT_KEY, DEFAULT_ANALYSIS_PROMPT)
    
    # ----- Deal prompts -----
    
    def get_deal_system_prompt(self) -> str:
        """Get the current deal system prompt."""
        self._load_prompts()
        defaults = _get_deal_defaults()
        return self._prompts.get(DEAL_SYSTEM_PROMPT_KEY, defaults[DEAL_SYSTEM_PROMPT_KEY])
    
    def get_deal_analysis_prompt(self) -> str:
        """Get the current deal analysis prompt template."""
        self._load_prompts()
        defaults = _get_deal_defaults()
        return self._prompts.get(DEAL_ANALYSIS_PROMPT_KEY, defaults[DEAL_ANALYSIS_PROMPT_KEY])
    
    def get_deal_scoring_system_prompt(self) -> str:
        """Get the current deal scoring system prompt."""
        self._load_prompts()
        defaults = _get_deal_defaults()
        return self._prompts.get(DEAL_SCORING_SYSTEM_PROMPT_KEY, defaults[DEAL_SCORING_SYSTEM_PROMPT_KEY])
    
    def get_deal_scoring_prompt(self) -> str:
        """Get the current deal scoring prompt template."""
        self._load_prompts()
        defaults = _get_deal_defaults()
        return self._prompts.get(DEAL_SCORING_PROMPT_KEY, defaults[DEAL_SCORING_PROMPT_KEY])
    
    # ----- Bulk operations -----
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts (leads + deals)."""
        self._load_prompts()
        defaults = self._get_all_defaults()
        return {key: self._prompts.get(key, default) for key, default in defaults.items()}
    
    def update_system_prompt(self, prompt: str) -> bool:
        """Update the lead system prompt."""
        self._load_prompts()
        self._prompts[LEAD_SYSTEM_PROMPT_KEY] = prompt
        return self._save_prompts()
    
    def update_analysis_prompt(self, prompt: str) -> bool:
        """Update the lead analysis prompt template."""
        self._load_prompts()
        self._prompts[LEAD_ANALYSIS_PROMPT_KEY] = prompt
        return self._save_prompts()
    
    def update_prompts(self, **kwargs: Optional[str]) -> bool:
        """
        Update any combination of prompts.
        
        Accepted keys:
        - system_prompt, analysis_prompt (leads)
        - deal_system_prompt, deal_analysis_prompt (deals)
        - deal_scoring_system_prompt, deal_scoring_prompt (deal scoring)
        """
        self._load_prompts()
        
        valid_keys = {
            LEAD_SYSTEM_PROMPT_KEY, LEAD_ANALYSIS_PROMPT_KEY,
            DEAL_SYSTEM_PROMPT_KEY, DEAL_ANALYSIS_PROMPT_KEY,
            DEAL_SCORING_SYSTEM_PROMPT_KEY, DEAL_SCORING_PROMPT_KEY,
        }
        
        for key, value in kwargs.items():
            if key in valid_keys and value is not None:
                self._prompts[key] = value
        
        return self._save_prompts()
    
    def reset_to_defaults(self) -> bool:
        """Reset all prompts to default values."""
        self._prompts = self._get_all_defaults()
        return self._save_prompts()


# Global instance
prompt_manager = PromptManager()
