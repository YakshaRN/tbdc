"""
DynamoDB User Service.

Manages user authentication data in DynamoDB.
Table: tbdc_users
"""
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings


class UserService:
    """
    DynamoDB-based user management service.
    
    Table Schema (tbdc_users):
    - email (PK): User's email address
    - password_hash: Hashed password
    - name: User's full name
    - role: User role (admin, user)
    - created_at: Account creation timestamp
    - last_login: Last login timestamp
    """
    
    TABLE_NAME = "tbdc_users"
    
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
            self._table = dynamodb.Table(self.TABLE_NAME)
        return self._table
    
    @property
    def is_enabled(self) -> bool:
        """Check if DynamoDB is configured."""
        return (
            bool(settings.AWS_ACCESS_KEY_ID)
            and bool(settings.AWS_SECRET_ACCESS_KEY)
        )
    
    def ensure_table_exists(self) -> bool:
        """Create the users table if it doesn't exist."""
        if not self.is_enabled:
            return False
        
        client = self._get_client()
        
        try:
            client.describe_table(TableName=self.TABLE_NAME)
            logger.debug(f"Table {self.TABLE_NAME} exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"Creating table {self.TABLE_NAME}...")
                try:
                    client.create_table(
                        TableName=self.TABLE_NAME,
                        KeySchema=[
                            {"AttributeName": "email", "KeyType": "HASH"},
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "email", "AttributeType": "S"},
                        ],
                        BillingMode="PAY_PER_REQUEST",
                    )
                    
                    # Wait for table to be created
                    waiter = client.get_waiter('table_exists')
                    waiter.wait(TableName=self.TABLE_NAME)
                    
                    logger.info(f"Table {self.TABLE_NAME} created successfully")
                    return True
                except Exception as create_error:
                    logger.error(f"Error creating table: {create_error}")
                    return False
            else:
                logger.error(f"Error checking table: {e}")
                return False
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 with salt
        hash_obj = hashlib.sha256((password + salt).encode())
        password_hash = hash_obj.hexdigest()
        
        return password_hash, salt
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return computed_hash == stored_hash
    
    def create_user(
        self, 
        email: str, 
        password: str, 
        name: str,
        role: str = "user"
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            name: User's full name
            role: User role (default: "user")
            
        Returns:
            Dict with success status and user data or error
        """
        if not self.is_enabled:
            return {"success": False, "error": "DynamoDB not configured"}
        
        # Ensure table exists
        if not self._table_checked:
            self.ensure_table_exists()
            self._table_checked = True
        
        try:
            table = self._get_table()
            
            # Check if user already exists
            response = table.get_item(Key={"email": email.lower()})
            if "Item" in response:
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            now = datetime.utcnow().isoformat()
            
            # Create user item
            user_item = {
                "email": email.lower(),
                "password_hash": password_hash,
                "salt": salt,
                "name": name,
                "role": role,
                "created_at": now,
                "last_login": None,
            }
            
            table.put_item(Item=user_item)
            
            logger.info(f"User created: {email}")
            
            return {
                "success": True,
                "user": {
                    "email": email.lower(),
                    "name": name,
                    "role": role,
                }
            }
            
        except ClientError as e:
            logger.error(f"Error creating user: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Dict with success status and user data or error
        """
        if not self.is_enabled:
            return {"success": False, "error": "DynamoDB not configured"}
        
        # Ensure table exists
        if not self._table_checked:
            self.ensure_table_exists()
            self._table_checked = True
        
        try:
            table = self._get_table()
            
            # Get user
            response = table.get_item(Key={"email": email.lower()})
            
            if "Item" not in response:
                return {"success": False, "error": "Invalid email or password"}
            
            user = response["Item"]
            
            # Verify password
            if not self._verify_password(password, user["password_hash"], user["salt"]):
                return {"success": False, "error": "Invalid email or password"}
            
            # Update last login
            now = datetime.utcnow().isoformat()
            table.update_item(
                Key={"email": email.lower()},
                UpdateExpression="SET last_login = :login_time",
                ExpressionAttributeValues={":login_time": now}
            )
            
            logger.info(f"User authenticated: {email}")
            
            return {
                "success": True,
                "user": {
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                }
            }
            
        except ClientError as e:
            logger.error(f"Error authenticating user: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error authenticating user: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        if not self.is_enabled:
            return None
        
        try:
            table = self._get_table()
            response = table.get_item(Key={"email": email.lower()})
            
            if "Item" in response:
                user = response["Item"]
                return {
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "created_at": user.get("created_at"),
                    "last_login": user.get("last_login"),
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update user data."""
        if not self.is_enabled:
            return False
        
        try:
            table = self._get_table()
            
            # Build update expression
            update_parts = []
            expr_values = {}
            
            if "name" in updates:
                update_parts.append("name = :name")
                expr_values[":name"] = updates["name"]
            
            if "role" in updates:
                update_parts.append("role = :role")
                expr_values[":role"] = updates["role"]
            
            if not update_parts:
                return True
            
            table.update_item(
                Key={"email": email.lower()},
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeValues=expr_values
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def change_password(self, email: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        if not self.is_enabled:
            return {"success": False, "error": "DynamoDB not configured"}
        
        try:
            table = self._get_table()
            
            # Get user
            response = table.get_item(Key={"email": email.lower()})
            
            if "Item" not in response:
                return {"success": False, "error": "User not found"}
            
            user = response["Item"]
            
            # Verify old password
            if not self._verify_password(old_password, user["password_hash"], user["salt"]):
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash new password
            new_hash, new_salt = self._hash_password(new_password)
            
            # Update password
            table.update_item(
                Key={"email": email.lower()},
                UpdateExpression="SET password_hash = :hash, salt = :salt",
                ExpressionAttributeValues={
                    ":hash": new_hash,
                    ":salt": new_salt
                }
            )
            
            logger.info(f"Password changed for: {email}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return {"success": False, "error": str(e)}


# Global instance
user_service = UserService()
