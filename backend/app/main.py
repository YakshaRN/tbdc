"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.middleware.zoho_token import ZohoTokenMiddleware
from app.api.v1.router import api_router
from app.services.zoho.token_manager import zoho_token_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize Zoho token manager
    await zoho_token_manager.initialize()
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
