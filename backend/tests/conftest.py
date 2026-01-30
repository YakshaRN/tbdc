"""
Pytest configuration and fixtures.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """
    Async HTTP client for testing API endpoints.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def mock_zoho_token():
    """
    Mock Zoho token manager.
    """
    with patch("app.services.zoho.token_manager.zoho_token_manager") as mock:
        mock.is_configured = True
        mock.get_access_token = AsyncMock(return_value="mock_access_token")
        mock.api_domain = "https://www.zohoapis.com"
        mock.token_status = {
            "configured": True,
            "has_token": True,
            "is_valid": True,
        }
        yield mock


@pytest.fixture
def mock_zoho_crm_service():
    """
    Mock Zoho CRM service.
    """
    with patch("app.services.zoho.crm_service.zoho_crm_service") as mock:
        yield mock
