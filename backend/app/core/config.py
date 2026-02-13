"""
Application configuration using python-dotenv.
"""
import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables from .env file
load_dotenv(ENV_FILE)


def get_list_from_env(key: str, default: List[str]) -> List[str]:
    """Parse a JSON-like list from environment variable."""
    value = os.getenv(key)
    if value:
        # Remove brackets and split by comma
        value = value.strip("[]")
        return [item.strip().strip('"').strip("'") for item in value.split(",")]
    return default


class Settings:
    """
    Application settings loaded from environment variables using python-dotenv.
    """
    
    # Base directory
    BASE_DIR: Path = BASE_DIR
    
    # Application
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "TBDC Backend")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = get_list_from_env(
        "BACKEND_CORS_ORIGINS", 
        ["http://localhost:3000", "http://localhost:8000"]
    )

    # Zoho OAuth Configuration
    ZOHO_CLIENT_ID: str = os.getenv("ZOHO_CLIENT_ID", "")
    ZOHO_CLIENT_SECRET: str = os.getenv("ZOHO_CLIENT_SECRET", "")
    ZOHO_REFRESH_TOKEN: str = os.getenv("ZOHO_REFRESH_TOKEN", "")
    ZOHO_REDIRECT_URI: str = os.getenv(
        "ZOHO_REDIRECT_URI", 
        "http://localhost:8000/api/v1/auth/zoho/callback"
    )
    
    # Zoho API Domain (varies by data center)
    # US: accounts.zoho.com, EU: accounts.zoho.eu, IN: accounts.zoho.in
    # AU: accounts.zoho.com.au, CN: accounts.zoho.com.cn, JP: accounts.zoho.jp
    ZOHO_ACCOUNTS_URL: str = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
    ZOHO_API_BASE_URL: str = os.getenv("ZOHO_API_BASE_URL", "https://www.zohoapis.com")
    
    # Token refresh buffer (refresh token X seconds before expiry)
    ZOHO_TOKEN_REFRESH_BUFFER: int = int(os.getenv("ZOHO_TOKEN_REFRESH_BUFFER", "300"))

    # Database (optional - for token persistence)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tokens.db")
    
    # AWS Bedrock Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # Bedrock Model Configuration
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    BEDROCK_MAX_TOKENS: int = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
    BEDROCK_TEMPERATURE: float = float(os.getenv("BEDROCK_TEMPERATURE", "0.3"))
    
    # DynamoDB Configuration (for caching lead analysis and prompts)
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "leads")
    DYNAMODB_DEAL_TABLE_NAME: str = os.getenv("DYNAMODB_DEAL_TABLE_NAME", "tbdc_deal_analysis")
    DYNAMODB_PROMPTS_TABLE_NAME: str = os.getenv("DYNAMODB_PROMPTS_TABLE_NAME", "prompts")
    DYNAMODB_ENABLED: bool = os.getenv("DYNAMODB_ENABLED", "true").lower() in ("true", "1", "yes")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "tbdc-super-secret-key-change-in-production")
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


# Create singleton settings instance
settings = Settings()
