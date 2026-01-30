"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.middleware.zoho_token import ZohoTokenMiddleware
from app.api.v1.router import api_router
from app.services.zoho.token_manager import zoho_token_manager
from app.services.dynamodb.lead_cache import lead_analysis_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize Zoho token manager
    await zoho_token_manager.initialize()
    
    # Startup: Initialize DynamoDB table for lead analysis caching
    if lead_analysis_cache.is_enabled:
        logger.info("DynamoDB caching is ENABLED, initializing table...")
        try:
            if lead_analysis_cache.ensure_table_exists():
                logger.info(f"DynamoDB table '{settings.DYNAMODB_TABLE_NAME}' is ready")
            else:
                logger.warning("DynamoDB table initialization failed - caching may not work")
        except Exception as e:
            logger.error(f"Error initializing DynamoDB table: {e}")
    else:
        logger.warning("DynamoDB caching is DISABLED - check AWS credentials and DYNAMODB_ENABLED setting")
        logger.info(f"  DYNAMODB_ENABLED: {settings.DYNAMODB_ENABLED}")
        logger.info(f"  AWS_ACCESS_KEY_ID set: {bool(settings.AWS_ACCESS_KEY_ID)}")
        logger.info(f"  AWS_SECRET_ACCESS_KEY set: {bool(settings.AWS_SECRET_ACCESS_KEY)}")
    
    yield
    # Shutdown: Cleanup resources
    await zoho_token_manager.close()


def create_application() -> FastAPI:
    """
    Application factory for creating FastAPI instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Backend API for Zoho CRM Integration",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add Zoho Token Management Middleware FIRST (runs second)
    app.add_middleware(ZohoTokenMiddleware)

    # Configure CORS LAST (runs first on incoming requests)
    # In Starlette/FastAPI, middleware added last runs first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/health/cache")
async def cache_health_check():
    """Check DynamoDB cache status."""
    cache_status = lead_analysis_cache.get_status()
    return {
        "status": "healthy" if cache_status.get("table_exists") else "degraded",
        "cache": cache_status,
    }
