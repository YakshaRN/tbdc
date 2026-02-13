"""
DynamoDB store for LLM prompts.

Stores all prompts (Leads + Application modules) in a single table.
Used as the only source of truth for prompts; no file or code defaults after seed.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings


# All prompt keys (must match prompt_manager and frontend)
PROMPT_KEYS = [
    "system_prompt",
    "analysis_prompt",
    "deal_system_prompt",
    "deal_analysis_prompt",
    "deal_scoring_system_prompt",
    "deal_scoring_prompt",
]


def _get_seed_prompts() -> Dict[str, str]:
    """Return initial prompt values used only when DynamoDB table is empty."""
    from app.services.dynamodb.prompt_seed import SEED_PROMPTS
    return dict(SEED_PROMPTS)


class PromptStore:
    """
    DynamoDB-backed store for LLM prompts.
    Table: prompt_key (PK, string) -> value (string), updated_at (string, optional).
    """

    def __init__(self):
        self._client = None
        self._table = None
        self._table_checked = False

    @property
    def table_name(self) -> str:
        return settings.DYNAMODB_PROMPTS_TABLE_NAME

    def _get_client(self):
        if self._client is None:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self._client = boto3.client("dynamodb", **kwargs)
        return self._client

    def _get_table(self):
        if self._table is None:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            dynamodb = boto3.resource("dynamodb", **kwargs)
            self._table = dynamodb.Table(settings.DYNAMODB_PROMPTS_TABLE_NAME)
        return self._table

    @property
    def is_enabled(self) -> bool:
        return settings.DYNAMODB_ENABLED

    def ensure_table_exists(self) -> bool:
        if not self.is_enabled:
            return False
        if self._table_checked:
            return True
        self._table_checked = True
        client = self._get_client()
        try:
            client.describe_table(TableName=self.table_name)
            logger.info(f"DynamoDB prompts table '{self.table_name}' exists")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                logger.error(f"Error checking prompts table: {e}")
                return False
        try:
            logger.info(f"Creating DynamoDB table '{self.table_name}'...")
            client.create_table(
                TableName=self.table_name,
                KeySchema=[{"AttributeName": "prompt_key", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "prompt_key", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            waiter = client.get_waiter("table_exists")
            waiter.wait(TableName=self.table_name)
            logger.info(f"Prompts table '{self.table_name}' created")
            return True
        except Exception as e:
            logger.error(f"Failed to create prompts table: {e}")
            return False

    def sync_seed_prompts(self) -> bool:
        """
        Sync seed prompts from prompt_seed.py to DynamoDB on startup.
        
        Overwrites all prompts in DynamoDB with the values from prompt_seed.py.
        This ensures code-level prompt changes are always deployed automatically.
        """
        if not self.is_enabled:
            logger.warning("DynamoDB is disabled, cannot sync seed prompts")
            return False
        if not self._table_checked:
            self.ensure_table_exists()
        
        seed = _get_seed_prompts()
        logger.info(f"Syncing {len(seed)} seed prompts to DynamoDB...")
        success = self.put_prompts(seed)
        if success:
            logger.info("Seed prompts synced to DynamoDB successfully")
        else:
            logger.error("Failed to sync seed prompts to DynamoDB")
        return success

    def get_all_prompts(self) -> Dict[str, str]:
        """Load all prompts from DynamoDB. If table is empty, seed and return."""
        if not self.is_enabled:
            logger.warning("DynamoDB is disabled, returning seed prompts")
            return _get_seed_prompts()

        if not self._table_checked:
            self.ensure_table_exists()
        table = self._get_table()
        result: Dict[str, str] = {}
        try:
            for key in PROMPT_KEYS:
                resp = table.get_item(Key={"prompt_key": key})
                if "Item" in resp and "value" in resp["Item"]:
                    result[key] = resp["Item"]["value"]
            if not result:
                seed = _get_seed_prompts()
                self.put_prompts(seed)
                return seed
            for key in PROMPT_KEYS:
                if key not in result:
                    result[key] = ""
            return result
        except Exception as e:
            logger.warning(f"Failed to load prompts from DynamoDB: {e}")
            return _get_seed_prompts()

    def put_prompts(self, prompts: Dict[str, str]) -> bool:
        """Save prompts to DynamoDB."""
        if not self.is_enabled:
            logger.warning("DynamoDB is disabled, cannot save prompts")
            return False
        if not self._table_checked:
            self.ensure_table_exists()
        table = self._get_table()
        now = datetime.utcnow().isoformat() + "Z"
        try:
            for key, value in prompts.items():
                if key not in PROMPT_KEYS:
                    continue
                table.put_item(
                    Item={
                        "prompt_key": key,
                        "value": value,
                        "updated_at": now,
                    }
                )
            logger.info(f"Saved {len(prompts)} prompts to DynamoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")
            return False


prompt_store = PromptStore()
