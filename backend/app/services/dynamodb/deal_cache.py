"""
DynamoDB service for caching deal analysis and marketing materials.

Stores LLM-generated analysis and marketing material recommendations
to avoid repeated API calls for the same deal.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings
from app.schemas.deal_analysis import DealAnalysis


class DealAnalysisCache:
    """
    DynamoDB-based cache for deal analysis and marketing materials.
    
    Uses the same table as lead cache but with 'deal_' prefix for deal IDs
    to avoid collisions.
    
    Table Schema:
    - lead_id (PK): Zoho Deal ID with 'deal_' prefix (e.g., 'deal_12345')
    - analysis: JSON string of DealAnalysis
    - marketing_materials: JSON string of marketing material list
    - similar_customers: JSON string of similar customers list
    - company_name: Company name for reference
    - fit_score: For easier querying/filtering
    - created_at: ISO timestamp when analysis was created
    - updated_at: ISO timestamp when analysis was last updated
    """
    
    DEAL_PREFIX = "deal_"
    
    def __init__(self):
        self._client = None
        self._table = None
        self._table_checked = False
    
    def _get_client(self):
        """Get or create DynamoDB client.
        
        Uses explicit credentials if provided, otherwise falls back to
        boto3's credential chain (IAM role, env vars, AWS config file).
        """
        if self._client is None:
            # Build kwargs - only include credentials if explicitly set
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
            self._client = boto3.client("dynamodb", **kwargs)
        return self._client
    
    def _get_table(self):
        """Get or create DynamoDB table resource.
        
        Uses explicit credentials if provided, otherwise falls back to
        boto3's credential chain (IAM role, env vars, AWS config file).
        """
        if self._table is None:
            # Build kwargs - only include credentials if explicitly set
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
            dynamodb = boto3.resource("dynamodb", **kwargs)
            self._table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
        return self._table
    
    def _get_cache_key(self, deal_id: str) -> str:
        """Generate cache key for a deal by adding prefix."""
        if deal_id.startswith(self.DEAL_PREFIX):
            return deal_id
        return f"{self.DEAL_PREFIX}{deal_id}"
    
    @property
    def is_enabled(self) -> bool:
        """Check if DynamoDB caching is enabled.
        
        Only checks if DYNAMODB_ENABLED is true. Credentials can come from:
        - Explicit AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars
        - EC2 IAM instance profile (auto-detected by boto3)
        - AWS CLI config file
        """
        if not settings.DYNAMODB_ENABLED:
            logger.debug("DynamoDB caching disabled via DYNAMODB_ENABLED=false")
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the DynamoDB cache."""
        has_explicit_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        status = {
            "enabled": self.is_enabled,
            "dynamodb_enabled_setting": settings.DYNAMODB_ENABLED,
            "credential_source": "explicit" if has_explicit_creds else "iam_role_or_default",
            "table_name": settings.DYNAMODB_TABLE_NAME,
            "region": settings.AWS_REGION,
            "table_exists": False,
            "cache_type": "deal",
        }
        
        if self.is_enabled:
            try:
                client = self._get_client()
                client.describe_table(TableName=settings.DYNAMODB_TABLE_NAME)
                status["table_exists"] = True
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    status["table_exists"] = False
                else:
                    status["error"] = str(e)
            except Exception as e:
                status["error"] = str(e)
        
        return status
    
    def get_analysis(self, deal_id: str) -> Optional[DealAnalysis]:
        """
        Retrieve cached analysis for a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            DealAnalysis if found in cache, None otherwise
        """
        result = self.get_cached_data(deal_id)
        if result:
            return result[0]  # Return just the analysis
        return None
    
    def get_cached_data(self, deal_id: str) -> Optional[Tuple[DealAnalysis, List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        Retrieve cached analysis, marketing materials, and similar customers for a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            Tuple of (DealAnalysis, marketing_materials, similar_customers) if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        cache_key = self._get_cache_key(deal_id)
        
        try:
            table = self._get_table()
            # Simple GetItem with partition key only (using lead_id column for deals too)
            response = table.get_item(Key={"lead_id": cache_key})
            
            if "Item" in response:
                item = response["Item"]
                analysis_data = json.loads(item["analysis"])
                
                # Get marketing materials if available
                marketing_materials = []
                if "marketing_materials" in item and item["marketing_materials"]:
                    marketing_materials = json.loads(item["marketing_materials"])
                
                # Get similar customers if available
                similar_customers = []
                if "similar_customers" in item and item["similar_customers"]:
                    similar_customers = json.loads(item["similar_customers"])
                
                logger.info(f"Cache HIT for deal {deal_id}")
                return (DealAnalysis(**analysis_data), marketing_materials, similar_customers)
            
            logger.debug(f"Cache MISS for deal {deal_id}")
            return None
            
        except ClientError as e:
            logger.error(f"Error retrieving deal from DynamoDB: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cached deal data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_cached_data for deal: {e}")
            return None
    
    def save_analysis(
        self, 
        deal_id: str, 
        analysis: DealAnalysis,
        marketing_materials: Optional[List[Dict[str, Any]]] = None,
        similar_customers: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Save analysis, marketing materials, and similar customers to cache.
        
        Args:
            deal_id: Zoho Deal ID
            analysis: DealAnalysis object to cache
            marketing_materials: List of marketing material dicts to cache
            similar_customers: List of similar customer dicts to cache
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        cache_key = self._get_cache_key(deal_id)
        
        try:
            table = self._get_table()
            now = datetime.utcnow().isoformat()
            
            # Convert analysis to dict, handling Pydantic model
            if hasattr(analysis, "model_dump"):
                analysis_dict = analysis.model_dump()
            else:
                analysis_dict = analysis.dict()
            
            item = {
                "lead_id": cache_key,  # Using lead_id column for deals with prefix
                "analysis": json.dumps(analysis_dict),
                "marketing_materials": json.dumps(marketing_materials or []),
                "similar_customers": json.dumps(similar_customers or []),
                "company_name": analysis_dict.get("company_name", "Unknown"),
                "fit_score": analysis_dict.get("fit_score", 5),
                "created_at": now,
                "updated_at": now,
                "record_type": "deal",  # Mark as deal record
            }
            
            table.put_item(Item=item)
            logger.info(f"Cached deal analysis, {len(marketing_materials or [])} materials, {len(similar_customers or [])} similar customers for deal {deal_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error saving deal to DynamoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in save_analysis for deal: {e}")
            return False
    
    def delete_analysis(self, deal_id: str) -> bool:
        """
        Delete cached analysis for a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        cache_key = self._get_cache_key(deal_id)
        
        try:
            table = self._get_table()
            table.delete_item(Key={"lead_id": cache_key})
            logger.info(f"Deleted cached analysis for deal {deal_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting deal from DynamoDB: {e}")
            return False
    
    def update_analysis(self, deal_id: str, analysis: DealAnalysis) -> bool:
        """
        Update existing cached analysis (or create if not exists).
        
        Args:
            deal_id: Zoho Deal ID
            analysis: Updated DealAnalysis object
            
        Returns:
            True if updated successfully, False otherwise
        """
        # For simplicity, just use save which will overwrite
        return self.save_analysis(deal_id, analysis)


# Create singleton instance
deal_analysis_cache = DealAnalysisCache()
