"""
DynamoDB service for caching deal analysis and marketing materials.

Stores LLM-generated analysis and marketing material recommendations
in a separate 'tbdc_deal_analysis' table to keep deal data isolated from leads.
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
    
    Uses a separate table from lead cache (configured via DYNAMODB_DEAL_TABLE_NAME).
    
    Table Schema (tbdc_deal_analysis):
    - deal_id (PK): Zoho Deal ID
    - analysis: JSON string of DealAnalysis
    - marketing_materials: JSON string of marketing material list
    - similar_customers: JSON string of similar customers list
    - company_name: Company/deal name for reference
    - fit_score: For easier querying/filtering
    - created_at: ISO timestamp when analysis was created
    - updated_at: ISO timestamp when analysis was last updated
    """
    
    def __init__(self):
        self._client = None
        self._table = None
        self._table_checked = False
    
    @property
    def table_name(self) -> str:
        """Get the deal analysis table name from settings."""
        return settings.DYNAMODB_DEAL_TABLE_NAME
    
    def _get_client(self):
        """Get or create DynamoDB client."""
        if self._client is None:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
            self._client = boto3.client("dynamodb", **kwargs)
        return self._client
    
    def _get_table(self):
        """Get or create DynamoDB table resource."""
        if self._table is None:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
            dynamodb = boto3.resource("dynamodb", **kwargs)
            self._table = dynamodb.Table(self.table_name)
        return self._table
    
    @property
    def is_enabled(self) -> bool:
        """Check if DynamoDB caching is enabled."""
        if not settings.DYNAMODB_ENABLED:
            logger.debug("DynamoDB caching disabled via DYNAMODB_ENABLED=false")
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the DynamoDB deal cache."""
        has_explicit_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        status = {
            "enabled": self.is_enabled,
            "dynamodb_enabled_setting": settings.DYNAMODB_ENABLED,
            "credential_source": "explicit" if has_explicit_creds else "iam_role_or_default",
            "table_name": self.table_name,
            "region": settings.AWS_REGION,
            "table_exists": False,
            "cache_type": "deal",
        }
        
        if self.is_enabled:
            try:
                client = self._get_client()
                client.describe_table(TableName=self.table_name)
                status["table_exists"] = True
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    status["table_exists"] = False
                else:
                    status["error"] = str(e)
            except Exception as e:
                status["error"] = str(e)
        
        return status
    
    def ensure_table_exists(self) -> bool:
        """
        Check if the DynamoDB table exists, create if not.
        Returns True if table exists or was created successfully.
        """
        if not self.is_enabled:
            logger.warning("DynamoDB is not enabled, skipping table creation")
            return False
        
        logger.info(f"Checking DynamoDB deal table '{self.table_name}' in region '{settings.AWS_REGION}'...")
        
        try:
            client = self._get_client()
        except Exception as e:
            logger.error(f"Failed to create DynamoDB client: {e}")
            return False
        
        try:
            response = client.describe_table(TableName=self.table_name)
            table_status = response.get("Table", {}).get("TableStatus", "UNKNOWN")
            logger.info(f"DynamoDB deal table '{self.table_name}' exists (status: {table_status})")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            if error_code == "ResourceNotFoundException":
                # Table doesn't exist, create it
                logger.info(f"Table not found, creating DynamoDB deal table '{self.table_name}'...")
                try:
                    client.create_table(
                        TableName=self.table_name,
                        KeySchema=[
                            {"AttributeName": "deal_id", "KeyType": "HASH"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "deal_id", "AttributeType": "S"},
                        ],
                        BillingMode="PAY_PER_REQUEST",
                    )
                    # Wait for table to be created
                    logger.info("Waiting for deal table to become active...")
                    waiter = client.get_waiter("table_exists")
                    waiter.wait(TableName=self.table_name)
                    logger.info(f"DynamoDB deal table '{self.table_name}' created successfully!")
                    return True
                except ClientError as create_error:
                    create_code = create_error.response["Error"]["Code"]
                    create_msg = create_error.response["Error"]["Message"]
                    logger.error(f"Failed to create DynamoDB deal table: [{create_code}] {create_msg}")
                    if create_code == "AccessDeniedException":
                        logger.error("AWS credentials don't have permission to create DynamoDB tables")
                        logger.error("Required permissions: dynamodb:CreateTable, dynamodb:DescribeTable")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error creating deal table: {e}")
                    return False
            elif error_code == "AccessDeniedException":
                logger.error(f"Access denied to DynamoDB: {error_message}")
                logger.error("AWS credentials don't have permission to access DynamoDB")
                return False
            else:
                logger.error(f"Error checking DynamoDB deal table: [{error_code}] {error_message}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error in ensure_table_exists: {e}")
            return False
    
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
            return result[0]
        return None
    
    def get_cached_data(self, deal_id: str) -> Optional[tuple]:
        """
        Retrieve cached analysis, marketing materials, similar customers, and meetings for a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            Tuple of (DealAnalysis, marketing_materials, similar_customers, meetings) if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        # Ensure table exists before first access
        if not self._table_checked:
            self.ensure_table_exists()
            self._table_checked = True
        
        try:
            table = self._get_table()
            response = table.get_item(Key={"deal_id": deal_id})
            
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
                
                # Get meetings if available
                meetings = []
                if "meetings" in item and item["meetings"]:
                    meetings = json.loads(item["meetings"])
                
                logger.info(f"Cache HIT for deal {deal_id}")
                return (DealAnalysis(**analysis_data), marketing_materials, similar_customers, meetings)
            
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
        similar_customers: Optional[List[Dict[str, Any]]] = None,
        meetings: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Save analysis, marketing materials, similar customers, and meetings to cache.
        
        Args:
            deal_id: Zoho Deal ID
            analysis: DealAnalysis object to cache
            marketing_materials: List of marketing material dicts to cache
            similar_customers: List of similar customer dicts to cache
            meetings: List of meeting note dicts to cache
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        # Ensure table exists before first access
        if not self._table_checked:
            self.ensure_table_exists()
            self._table_checked = True
        
        try:
            table = self._get_table()
            now = datetime.utcnow().isoformat()
            
            # Convert analysis to dict, handling Pydantic model
            if hasattr(analysis, "model_dump"):
                analysis_dict = analysis.model_dump()
            else:
                analysis_dict = analysis.dict()
            
            item = {
                "deal_id": deal_id,
                "analysis": json.dumps(analysis_dict),
                "marketing_materials": json.dumps(marketing_materials or []),
                "similar_customers": json.dumps(similar_customers or []),
                "meetings": json.dumps(meetings or []),
                "company_name": analysis_dict.get("company_name", "Unknown"),
                "fit_score": analysis_dict.get("fit_score", 5),
                "created_at": now,
                "updated_at": now,
            }
            
            table.put_item(Item=item)
            logger.info(
                f"Cached deal analysis, {len(marketing_materials or [])} materials, "
                f"{len(similar_customers or [])} similar customers, "
                f"{len(meetings or [])} meetings for deal {deal_id}"
            )
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
        
        try:
            table = self._get_table()
            table.delete_item(Key={"deal_id": deal_id})
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
        return self.save_analysis(deal_id, analysis)


# Create singleton instance
deal_analysis_cache = DealAnalysisCache()
