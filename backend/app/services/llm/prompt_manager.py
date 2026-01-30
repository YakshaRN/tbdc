"""
Prompt Manager Service.

Manages system and analysis prompts with persistence to a JSON file.
Allows runtime updates without restarting the server.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from app.core.config import settings


# Default prompts (used if no saved prompts exist)
DEFAULT_SYSTEM_PROMPT = """You are an analyst for TBDC's Pivot program and an expert B2B lead qualification specialist.

Your role is to evaluate ONE Indian or global startup at a time for Canada and North America fit.
You assess the company's product, business model, GTM motion, funding maturity, and suitability
for entering the Canadian market.

You must base your analysis primarily on the company's official website
(homepage, product, solutions, or industries pages).
If the website is vague or unclear, you must explicitly state this, infer only at a high level,
and lower your confidence. Never invent product features or use cases.

Your output is used by strategy and sales teams to:
- Decide whether the company is worth outreach
- Prioritize leads for the TBDC Pivot program
- Identify key Canada-specific GTM considerations

Always respond with valid JSON only.
Do not include explanations, markdown, or any text outside the JSON object."""

DEFAULT_ANALYSIS_PROMPT = """Evaluate the following company for Canada fit under TBDC's Pivot program.

Company Input:
{lead_data}

Evaluation rules:
- Always review the official website first.
- Use third-party sources only to confirm or resolve ambiguity.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.

Respond with a JSON object using the structure below:

{{
  "company_name": "Company name or primary domain",

  "country": "Country where the company is based (infer from address, phone, or company info)",
  "region": "Geographic region (e.g., North America, Europe, APAC, etc.)",

  "product_description": "One-line description of what the product does and for whom (or 'Unclear from site' if applicable)",

  "vertical": "Industry vertical or sector (e.g., Fintech - SME, Healthtech, SaaS, Logistics, Data/AI, etc.)",

  "business_model": "Business model type (e.g., B2B, B2C, B2B2C, Marketplace, Subscription, Services-led)",

  "motion": "Go-to-market motion (SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy)",

  "raise_stage": "Funding stage if identifiable (Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown)",

  "company_size": "Estimated company size (Startup, SMB, Mid-Market, Enterprise, Unknown)",

  "likely_icp_canada": "Most likely Canadian customer profile if applicable (e.g., SMBs, mid-market enterprises, regulated industries)",

  "fit_score": "Integer from 1–10 indicating how strong the Canada market fit appears to be",

  "fit_assessment": "Brief assessment explaining why this company is or is not a good fit for Canada and TBDC Pivot",

  "key_insights": [
    "3–5 concise insights about the company's product, GTM readiness, or Canada relevance"
  ],

  "questions_to_ask": [
    "5–7 strategic questions the team should ask to validate Canada entry, ICP, differentiation, and GTM feasibility"
  ],

  "confidence_level": "High, Medium, or Low",

  "notes": [
    "Any important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product, or strong incumbents in Canada"
  ]
}}

Respond ONLY with the JSON object and no additional text."""


class PromptManager:
    """
    Manages LLM prompts with file-based persistence.
    
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
        
        # Ensure defaults are set
        if "system_prompt" not in self._prompts:
            self._prompts["system_prompt"] = DEFAULT_SYSTEM_PROMPT
        if "analysis_prompt" not in self._prompts:
            self._prompts["analysis_prompt"] = DEFAULT_ANALYSIS_PROMPT
        
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
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        self._load_prompts()
        return self._prompts.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    
    def get_analysis_prompt(self) -> str:
        """Get the current analysis prompt template."""
        self._load_prompts()
        return self._prompts.get("analysis_prompt", DEFAULT_ANALYSIS_PROMPT)
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts."""
        self._load_prompts()
        return {
            "system_prompt": self._prompts.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            "analysis_prompt": self._prompts.get("analysis_prompt", DEFAULT_ANALYSIS_PROMPT),
        }
    
    def update_system_prompt(self, prompt: str) -> bool:
        """Update the system prompt."""
        self._load_prompts()
        self._prompts["system_prompt"] = prompt
        return self._save_prompts()
    
    def update_analysis_prompt(self, prompt: str) -> bool:
        """Update the analysis prompt template."""
        self._load_prompts()
        self._prompts["analysis_prompt"] = prompt
        return self._save_prompts()
    
    def update_prompts(self, system_prompt: Optional[str] = None, analysis_prompt: Optional[str] = None) -> bool:
        """Update one or both prompts."""
        self._load_prompts()
        
        if system_prompt is not None:
            self._prompts["system_prompt"] = system_prompt
        if analysis_prompt is not None:
            self._prompts["analysis_prompt"] = analysis_prompt
        
        return self._save_prompts()
    
    def reset_to_defaults(self) -> bool:
        """Reset prompts to default values."""
        self._prompts = {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "analysis_prompt": DEFAULT_ANALYSIS_PROMPT,
        }
        return self._save_prompts()


# Global instance
prompt_manager = PromptManager()
