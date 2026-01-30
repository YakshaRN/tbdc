"""
Lead endpoint tests.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.anyio
async def test_list_leads(client: AsyncClient, mock_zoho_token, mock_zoho_crm_service):
    """Test listing leads endpoint."""
    # Mock the CRM service response
    mock_zoho_crm_service.get_leads = AsyncMock(return_value={
        "data": [
            {"id": "123", "Last_Name": "Test", "Email": "test@example.com"}
        ],
        "info": {
            "page": 1,
            "per_page": 50,
            "count": 1,
            "more_records": False,
        }
    })
    
    with patch("app.api.v1.endpoints.leads.zoho_crm_service", mock_zoho_crm_service):
        response = await client.get("/api/v1/leads/")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.anyio
async def test_get_lead_by_id(client: AsyncClient, mock_zoho_token, mock_zoho_crm_service):
    """Test getting a single lead by ID."""
    mock_zoho_crm_service.get_lead_by_id = AsyncMock(return_value={
        "data": [
            {"id": "123", "Last_Name": "Test", "Email": "test@example.com"}
        ]
    })
    
    with patch("app.api.v1.endpoints.leads.zoho_crm_service", mock_zoho_crm_service):
        response = await client.get("/api/v1/leads/123")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
