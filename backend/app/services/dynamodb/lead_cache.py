"""
DynamoDB service for caching lead analysis and marketing materials.

Stores LLM-generated analysis and marketing material recommendations
to avoid repeated API calls for the same lead.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings
from app.schemas.lead_analysis import LeadAnalysis


class LeadAnalysisCache:
    """
    DynamoDB-based cache for lead analysis and marketing materials.
    
    Table Schema:
    - lead_id (PK): Zoho Lead ID
    - analysis: JSON string of LeadAnalysis
    - marketing_materials: JSON string of marketing material list
    - created_at: ISO timestamp when analysis was created
    - updated_at: ISO timestamp when analysis was last updated
    - company_name: For easier querying
    - fit_score: For easier querying/filtering
    """
    
    def __init__(self):
        self._client = None
        self._table = None
        self._table_checked = False
    
    def _get_client(self):
        """Get or create DynamoDB client."""
        if self._client is None:
            self._client = boto3.client(
                "dynamodb",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
        return self._client
    
    def _get_table(self):
        """Get or create DynamoDB table resource."""
        if self._table is None:
            dynamodb = boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            self._table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
        return self._table
    
    @property
    def is_enabled(self) -> bool:
        """Check if DynamoDB caching is enabled and configured."""
        enabled = (
            settings.DYNAMODB_ENABLED
            and bool(settings.AWS_ACCESS_KEY_ID)
            and bool(settings.AWS_SECRET_ACCESS_KEY)
        )
        if not enabled:
            if not settings.DYNAMODB_ENABLED:
                logger.debug("DynamoDB caching disabled via DYNAMODB_ENABLED=false")
            elif not settings.AWS_ACCESS_KEY_ID:
                logger.debug("DynamoDB caching disabled: AWS_ACCESS_KEY_ID not set")
            elif not settings.AWS_SECRET_ACCESS_KEY:
                logger.debug("DynamoDB caching disabled: AWS_SECRET_ACCESS_KEY not set")
        return enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the DynamoDB cache."""
        status = {
            "enabled": self.is_enabled,
            "dynamodb_enabled_setting": settings.DYNAMODB_ENABLED,
            "aws_credentials_set": bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY),
            "table_name": settings.DYNAMODB_TABLE_NAME,
            "region": settings.AWS_REGION,
            "table_exists": False,
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
    
    def ensure_table_exists(self) -> bool:
        """
        Check if the DynamoDB table exists, create if not.
        Returns True if table exists or was created successfully.
        """
        if not self.is_enabled:
            logger.warning("DynamoDB is not enabled, skipping table creation")
            return False
        
        logger.info(f"Checking DynamoDB table '{settings.DYNAMODB_TABLE_NAME}' in region '{settings.AWS_REGION}'...")
        
        try:
            client = self._get_client()
        except Exception as e:
            logger.error(f"Failed to create DynamoDB client: {e}")
            return False
        
        try:
            response = client.describe_table(TableName=settings.DYNAMODB_TABLE_NAME)
            table_status = response.get("Table", {}).get("TableStatus", "UNKNOWN")
            logger.info(f"DynamoDB table '{settings.DYNAMODB_TABLE_NAME}' exists (status: {table_status})")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            if error_code == "ResourceNotFoundException":
                # Table doesn't exist, create it
                logger.info(f"Table not found, creating DynamoDB table '{settings.DYNAMODB_TABLE_NAME}'...")
                try:
                    client.create_table(
                        TableName=settings.DYNAMODB_TABLE_NAME,
                        KeySchema=[
                            {"AttributeName": "lead_id", "KeyType": "HASH"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "lead_id", "AttributeType": "S"},
                        ],
                        BillingMode="PAY_PER_REQUEST",  # On-demand pricing
                    )
                    # Wait for table to be created
                    logger.info("Waiting for table to become active...")
                    waiter = client.get_waiter("table_exists")
                    waiter.wait(TableName=settings.DYNAMODB_TABLE_NAME)
                    logger.info(f"DynamoDB table '{settings.DYNAMODB_TABLE_NAME}' created successfully!")
                    return True
                except ClientError as create_error:
                    create_code = create_error.response["Error"]["Code"]
                    create_msg = create_error.response["Error"]["Message"]
                    logger.error(f"Failed to create DynamoDB table: [{create_code}] {create_msg}")
                    if create_code == "AccessDeniedException":
                        logger.error("AWS credentials don't have permission to create DynamoDB tables")
                        logger.error("Required permissions: dynamodb:CreateTable, dynamodb:DescribeTable")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error creating table: {e}")
                    return False
            elif error_code == "AccessDeniedException":
                logger.error(f"Access denied to DynamoDB: {error_message}")
                logger.error("AWS credentials don't have permission to access DynamoDB")
                logger.error("Required permissions: dynamodb:DescribeTable, dynamodb:GetItem, dynamodb:PutItem, dynamodb:DeleteItem")
                return False
            else:
                logger.error(f"Error checking DynamoDB table: [{error_code}] {error_message}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error in ensure_table_exists: {e}")
            return False
    
    def get_analysis(self, lead_id: str) -> Optional[LeadAnalysis]:
        """
        Retrieve cached analysis for a lead.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            LeadAnalysis if found in cache, None otherwise
        """
        result = self.get_cached_data(lead_id)
        if result:
            return result[0]  # Return just the analysis
        return None
    
    def get_cached_data(self, lead_id: str) -> Optional[Tuple[LeadAnalysis, List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        Retrieve cached analysis, marketing materials, and similar customers for a lead.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            Tuple of (LeadAnalysis, marketing_materials, similar_customers) if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        # Ensure table exists before first access
        if not self._table_checked:
            self.ensure_table_exists()
            self._table_checked = True
        
        try:
            table = self._get_table()
            response = table.get_item(Key={"lead_id": lead_id})
            
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
                
                logger.info(f"Cache HIT for lead {lead_id}")
                return (LeadAnalysis(**analysis_data), marketing_materials, similar_customers)
            
            logger.debug(f"Cache MISS for lead {lead_id}")
            return None
            
        except ClientError as e:
            logger.error(f"Error retrieving from DynamoDB: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cached data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_cached_data: {e}")
            return None
    
    def save_analysis(
        self, 
        lead_id: str, 
        analysis: LeadAnalysis,
        marketing_materials: Optional[List[Dict[str, Any]]] = None,
        similar_customers: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Save analysis, marketing materials, and similar customers to cache.
        
        Args:
            lead_id: Zoho Lead ID
            analysis: LeadAnalysis object to cache
            marketing_materials: List of marketing material dicts to cache
            similar_customers: List of similar customer dicts to cache
            
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
                "lead_id": lead_id,
                "analysis": json.dumps(analysis_dict),
                "marketing_materials": json.dumps(marketing_materials or []),
                "similar_customers": json.dumps(similar_customers or []),
                "company_name": analysis_dict.get("company_name", "Unknown"),
                "fit_score": analysis_dict.get("fit_score", 5),
                "created_at": now,
                "updated_at": now,
            }
            
            table.put_item(Item=item)
            logger.info(f"Cached analysis, {len(marketing_materials or [])} materials, {len(similar_customers or [])} similar customers for lead {lead_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error saving to DynamoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in save_analysis: {e}")
            return False
    
    def delete_analysis(self, lead_id: str) -> bool:
        """
        Delete cached analysis for a lead.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        try:
            table = self._get_table()
            table.delete_item(Key={"lead_id": lead_id})
            logger.info(f"Deleted cached analysis for lead {lead_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting from DynamoDB: {e}")
            return False
    
    def update_analysis(self, lead_id: str, analysis: LeadAnalysis) -> bool:
        """
        Update existing cached analysis (or create if not exists).
        
        Args:
            lead_id: Zoho Lead ID
            analysis: Updated LeadAnalysis object
            
        Returns:
            True if updated successfully, False otherwise
        """
        # For simplicity, just use save which will overwrite
        return self.save_analysis(lead_id, analysis)


# Create singleton instance
lead_analysis_cache = LeadAnalysisCache()
