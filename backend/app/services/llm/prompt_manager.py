"""
Prompt Manager Service.

Manages all LLM prompts (Leads and Deals/Application modules)
with persistence in DynamoDB only. No file or code defaults at runtime.
"""
from typing import Dict, Optional
from loguru import logger

from app.services.dynamodb.prompt_store import (
    prompt_store,
    PROMPT_KEYS,
    _get_seed_prompts,
)

# Keys used for storage (must match prompt_store.PROMPT_KEYS and frontend)
LEAD_SYSTEM_PROMPT_KEY = "system_prompt"
LEAD_ANALYSIS_PROMPT_KEY = "analysis_prompt"
DEAL_SYSTEM_PROMPT_KEY = "deal_system_prompt"
DEAL_ANALYSIS_PROMPT_KEY = "deal_analysis_prompt"
DEAL_SCORING_SYSTEM_PROMPT_KEY = "deal_scoring_system_prompt"
DEAL_SCORING_PROMPT_KEY = "deal_scoring_prompt"


class PromptManager:
    """
    Manages all LLM prompts (Leads + Deals) with DynamoDB as the only persistence.
    No in-memory cache: every read goes to DynamoDB.
    """

    def _get(self, key: str) -> str:
        """Fetch prompts from DynamoDB and return the value for key."""
        return prompt_store.get_all_prompts().get(key, "")

    # ----- Lead prompts -----

    def get_system_prompt(self) -> str:
        return self._get(LEAD_SYSTEM_PROMPT_KEY)

    def get_analysis_prompt(self) -> str:
        return self._get(LEAD_ANALYSIS_PROMPT_KEY)

    # ----- Deal prompts -----

    def get_deal_system_prompt(self) -> str:
        return self._get(DEAL_SYSTEM_PROMPT_KEY)

    def get_deal_analysis_prompt(self) -> str:
        return self._get(DEAL_ANALYSIS_PROMPT_KEY)

    def get_deal_scoring_system_prompt(self) -> str:
        return self._get(DEAL_SCORING_SYSTEM_PROMPT_KEY)

    def get_deal_scoring_prompt(self) -> str:
        return self._get(DEAL_SCORING_PROMPT_KEY)

    # ----- Bulk operations -----

    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts from DynamoDB (no cache)."""
        return prompt_store.get_all_prompts()

    def update_system_prompt(self, prompt: str) -> bool:
        return prompt_store.put_prompts({LEAD_SYSTEM_PROMPT_KEY: prompt})

    def update_analysis_prompt(self, prompt: str) -> bool:
        return prompt_store.put_prompts({LEAD_ANALYSIS_PROMPT_KEY: prompt})

    def update_prompts(self, **kwargs: Optional[str]) -> bool:
        """
        Update any combination of prompts. Saves to DynamoDB.
        Accepted keys: system_prompt, analysis_prompt, deal_system_prompt,
        deal_analysis_prompt, deal_scoring_system_prompt, deal_scoring_prompt.
        """
        valid = {
            "system_prompt": LEAD_SYSTEM_PROMPT_KEY,
            "analysis_prompt": LEAD_ANALYSIS_PROMPT_KEY,
            "deal_system_prompt": DEAL_SYSTEM_PROMPT_KEY,
            "deal_analysis_prompt": DEAL_ANALYSIS_PROMPT_KEY,
            "deal_scoring_system_prompt": DEAL_SCORING_SYSTEM_PROMPT_KEY,
            "deal_scoring_prompt": DEAL_SCORING_PROMPT_KEY,
        }
        to_save = {valid[k]: v for k, v in kwargs.items() if k in valid and v is not None}
        return prompt_store.put_prompts(to_save) if to_save else True

    def reset_to_defaults(self) -> bool:
        """Reset all prompts to seed values and save to DynamoDB."""
        return prompt_store.put_prompts(_get_seed_prompts())


prompt_manager = PromptManager()
