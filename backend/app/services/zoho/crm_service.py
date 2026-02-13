"""
Zoho CRM Service.

Provides methods for interacting with Zoho CRM API.
"""
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger

from app.services.zoho.token_manager import zoho_token_manager
from app.core.config import settings
from app.core.exceptions import ZohoAPIException, RateLimitException



class ZohoCRMService:
    """
    Service class for Zoho CRM API operations.
    
    Handles:
    - Lead operations (get, list, create, update, delete)
    - Contact operations
    - Deal operations
    - Custom module operations
    """
    
    CRM_API_VERSION = "v7"  # Latest stable version
    
    # Default fields to fetch for each module (required in v7)
    DEFAULT_LEAD_FIELDS = [
        "id", "First_Name", "Last_Name", "Email", "Phone", "Mobile",
        "Company", "Title", "Industry", "Lead_Source", "Lead_Status",
        "Website", "LinkedIn_Profile", "Description", "Street", "City",
        "State", "Zip_Code", "Country", "Created_Time", "Modified_Time",
        "Owner"
    ]
    
    DEFAULT_CONTACT_FIELDS = [
        "id", "First_Name", "Last_Name", "Email", "Phone", "Mobile",
        "Account_Name", "Title", "Department", "Mailing_Street", 
        "Mailing_City", "Mailing_State", "Mailing_Zip", "Mailing_Country",
        "Created_Time", "Modified_Time", "Owner"
    ]
    
    DEFAULT_DEAL_FIELDS = [
        "id", "Deal_Name", "Account_Name", "Contact_Name", "Amount",
        "Stage", "Closing_Date", "Probability", "Type", "Lead_Source",
        "Created_Time", "Modified_Time", "Owner"
    ]
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
    
    def _get_base_url(self) -> str:
        """Get the base URL for CRM API."""
        return f"{zoho_token_manager.api_domain}/crm/{self.CRM_API_VERSION}"
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with valid access token."""
        access_token = await zoho_token_manager.get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Zoho CRM API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/Leads")
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            API response data
            
        Raises:
            ZohoAPIException: For API errors
            RateLimitException: When rate limited
        """
        client = await self._get_client()
        headers = await self._get_headers()
        url = f"{self._get_base_url()}{endpoint}"
        
        logger.debug(f"[Zoho] >>> {method} {endpoint}")
        logger.debug(f"[Zoho] Full URL: {url}")
        if params:
            logger.debug(f"[Zoho] Params: {params}")
        if json_data:
            logger.debug(f"[Zoho] Body: {json_data}")
        
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            
            logger.debug(f"[Zoho] <<< {method} {endpoint} — status: {response.status_code}")
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.error(f"[Zoho] Rate limited (429) on {method} {endpoint}")
                raise RateLimitException()
            
            # Handle authentication errors (token might be invalid)
            if response.status_code == 401:
                logger.warning(f"[Zoho] Token invalid (401) on {method} {endpoint}, attempting refresh...")
                await zoho_token_manager.refresh_access_token()
                # Retry with new token
                headers = await self._get_headers()
                logger.debug(f"[Zoho] Retrying {method} {endpoint} after token refresh")
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                logger.debug(f"[Zoho] <<< {method} {endpoint} (retry) — status: {response.status_code}")
            
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("message", response.text)
                logger.error(f"[Zoho] API Error on {method} {endpoint}: {response.status_code} - {error_message}")
                raise ZohoAPIException(
                    detail=f"Zoho API Error: {error_message}",
                    status_code=response.status_code,
                )
            
            result = response.json() if response.text else {}
            # Log record count if present
            record_count = len(result.get("data", [])) if isinstance(result.get("data"), list) else None
            if record_count is not None:
                logger.debug(f"[Zoho] {method} {endpoint} returned {record_count} record(s)")
            return result
            
        except httpx.RequestError as e:
            logger.error(f"[Zoho] Network error on {method} {endpoint}: {e}")
            raise ZohoAPIException(detail=f"Network error: {str(e)}")
    
    # ==================== LEAD OPERATIONS ====================
    
    async def get_leads(
        self,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        Fetch leads from Zoho CRM.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of records per page (max 200)
            fields: List of fields to retrieve (required in v7)
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Dict containing leads data and pagination info
        """
        # Use default fields if none specified (required in Zoho CRM API v7)
        field_list = fields if fields else self.DEFAULT_LEAD_FIELDS
        
        params = {
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),  # Max 200 per page
        }
        
        if sort_by:
            params["sort_by"] = sort_by
            params["sort_order"] = sort_order
        
        return await self._make_request("GET", "/Leads", params=params)
    
    async def get_lead_by_id(self, lead_id: str) -> Dict[str, Any]:
        """
        Get a specific lead by ID.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            Lead data
        """
        return await self._make_request("GET", f"/Leads/{lead_id}")
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lead in Zoho CRM.
        
        Args:
            lead_data: Lead data following Zoho's schema
            
        Returns:
            Created lead response
        """
        payload = {"data": [lead_data]}
        return await self._make_request("POST", "/Leads", json_data=payload)
    
    async def update_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing lead.
        
        Args:
            lead_id: Zoho Lead ID
            lead_data: Updated lead data
            
        Returns:
            Updated lead response
        """
        payload = {"data": [{"id": lead_id, **lead_data}]}
        return await self._make_request("PUT", "/Leads", json_data=payload)
    
    async def delete_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Delete a lead.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            Deletion response
        """
        return await self._make_request("DELETE", f"/Leads/{lead_id}")
    
    async def search_leads(
        self,
        criteria: str,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search leads using Zoho's search criteria.
        
        Args:
            criteria: Search criteria (e.g., "(Email:equals:test@example.com)")
            page: Page number
            per_page: Records per page
            fields: Fields to retrieve
            
        Returns:
            Search results
        """
        # Use default fields if none specified (required in Zoho CRM API v7)
        field_list = fields if fields else self.DEFAULT_LEAD_FIELDS

        
        params = {
            "criteria": criteria,
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),
        }
        return await self._make_request("GET", "/Leads/search", params=params)
    
    async def search_all_leads(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        max_records: int = 2000,
    ) -> Dict[str, Any]:
        """
        Search and fetch ALL leads matching criteria by paginating through all pages.
        
        Args:
            criteria: Search criteria (e.g., "(Lead_Source:equals:LinkedIn Ads)")
            fields: Fields to retrieve
            max_records: Maximum records to fetch (safety limit)
            
        Returns:
            Combined results with all matching leads
        """
        all_leads = []
        page = 1
        per_page = 200  # Max allowed by Zoho
        
        while len(all_leads) < max_records:
            try:
                result = await self.search_leads(
                    criteria=criteria,
                    page=page,
                    per_page=per_page,
                    fields=fields,
                )
                
                leads = result.get("data", [])
                if not leads:
                    break
                    
                all_leads.extend(leads)
                logger.info(f"Fetched page {page}: {len(leads)} leads (total: {len(all_leads)})")
                
                # Check if there are more records
                info = result.get("info", {})
                if not info.get("more_records", False):
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total leads fetched: {len(all_leads)}")
        
        return {
            "data": all_leads,
            "info": {
                "count": len(all_leads),
                "page": 1,
                "per_page": len(all_leads),
                "more_records": False,
            }
        }
    
    # ==================== ATTACHMENT OPERATIONS ====================
    
    # Default fields for Attachments
    DEFAULT_ATTACHMENT_FIELDS = [
        "id", "File_Name", "Size", "Created_Time", "Modified_Time",
        "Created_By", "Modified_By", "$file_id", "$type"
    ]
    
    async def get_lead_attachments(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Get list of attachments for a lead.
        
        Args:
            lead_id: Zoho Lead ID
            
        Returns:
            List of attachment metadata (id, file_name, size, etc.)
        """
        try:
            params = {
                "fields": ",".join(self.DEFAULT_ATTACHMENT_FIELDS)
            }
            result = await self._make_request(
                "GET", 
                f"/Leads/{lead_id}/Attachments",
                params=params
            )
            return result.get("data", [])
        except Exception as e:
            logger.warning(f"Error fetching attachments for lead {lead_id}: {e}")
            return []
    
    async def download_attachment(self, lead_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download an attachment file content.
        
        Args:
            lead_id: Zoho Lead ID
            attachment_id: Attachment ID
            
        Returns:
            File content as bytes, or None if failed
        """
        try:
            client = await self._get_client()
            headers = await self._get_headers()
            # Remove Content-Type for download
            headers.pop("Content-Type", None)
            
            url = f"{self._get_base_url()}/Leads/{lead_id}/Attachments/{attachment_id}"
            
            logger.info(f"[Zoho] >>> GET /Leads/{lead_id}/Attachments/{attachment_id} (download)")
            response = await client.get(url, headers=headers)
            logger.info(f"[Zoho] <<< GET /Leads/{lead_id}/Attachments/{attachment_id} — status: {response.status_code}, size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"[Zoho] Failed to download attachment {attachment_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[Zoho] Error downloading attachment {attachment_id}: {e}")
            return None
    
    async def get_lead_attachments_with_content(
        self, 
        lead_id: str,
        supported_extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a lead with their file content.
        
        Args:
            lead_id: Zoho Lead ID
            supported_extensions: List of file extensions to download (e.g., ['.pdf', '.docx'])
                                 If None, downloads common document types.
            
        Returns:
            List of attachment dicts with 'content' key containing bytes
        """
        if supported_extensions is None:
            supported_extensions = [
                '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                '.txt', '.rtf', '.xls', '.xlsx'
            ]
        
        attachments = await self.get_lead_attachments(lead_id)
        
        result = []
        for attachment in attachments:
            file_name = attachment.get("File_Name", "")
            attachment_id = attachment.get("id")
            
            if not attachment_id:
                continue
            
            # Check if file extension is supported
            ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""
            if ext not in supported_extensions:
                logger.debug(f"Skipping unsupported file type: {file_name}")
                continue
            
            # Download the content
            content = await self.download_attachment(lead_id, attachment_id)
            
            if content:
                result.append({
                    "id": attachment_id,
                    "file_name": file_name,
                    "extension": ext,
                    "size": attachment.get("Size", len(content)),
                    "content": content,
                    "created_time": attachment.get("Created_Time"),
                })
                logger.info(f"Downloaded attachment: {file_name} ({len(content)} bytes)")
            else:
                logger.warning(f"Failed to download: {file_name}")
        
        return result
    
    # ==================== CONTACT OPERATIONS ====================
    
    async def get_contacts(
        self,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fetch contacts from Zoho CRM."""
        # Use default fields if none specified (required in Zoho CRM API v7)
        field_list = fields if fields else self.DEFAULT_CONTACT_FIELDS
        
        params = {
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),
        }
        return await self._make_request("GET", "/Contacts", params=params)
    
    async def get_contact_by_id(self, contact_id: str) -> Dict[str, Any]:
        """Get a specific contact by ID."""
        return await self._make_request("GET", f"/Contacts/{contact_id}")
    
    # ==================== DEAL OPERATIONS ====================
    
    async def get_deals(
        self,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fetch deals from Zoho CRM."""
        # Use default fields if none specified (required in Zoho CRM API v7)
        field_list = fields if fields else self.DEFAULT_DEAL_FIELDS
        
        params = {
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),
        }
        return await self._make_request("GET", "/Deals", params=params)
    
    async def get_deal_by_id(self, deal_id: str) -> Dict[str, Any]:
        """Get a specific deal by ID."""
        return await self._make_request("GET", f"/Deals/{deal_id}")
    
    async def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new deal in Zoho CRM.
        
        Args:
            deal_data: Deal data following Zoho's schema
            
        Returns:
            Created deal response
        """
        payload = {"data": [deal_data]}
        return await self._make_request("POST", "/Deals", json_data=payload)
    
    async def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing deal.
        
        Args:
            deal_id: Zoho Deal ID
            deal_data: Updated deal data
            
        Returns:
            Updated deal response
        """
        payload = {"data": [{"id": deal_id, **deal_data}]}
        return await self._make_request("PUT", "/Deals", json_data=payload)
    
    async def delete_deal(self, deal_id: str) -> Dict[str, Any]:
        """
        Delete a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            Deletion response
        """
        return await self._make_request("DELETE", f"/Deals/{deal_id}")
    
    async def search_deals(
        self,
        criteria: str,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search deals using Zoho's search criteria.
        
        Args:
            criteria: Search criteria (e.g., "(Stage:equals:Qualification)")
            page: Page number
            per_page: Records per page
            fields: Fields to retrieve
            
        Returns:
            Search results
        """
        # Use default fields if none specified (required in Zoho CRM API v7)
        field_list = fields if fields else self.DEFAULT_DEAL_FIELDS
        
        params = {
            "criteria": criteria,
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),
        }
        return await self._make_request("GET", "/Deals/search", params=params)
    
    async def search_all_deals(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        max_records: int = 2000,
    ) -> Dict[str, Any]:
        """
        Search and fetch ALL deals matching criteria by paginating through all pages.
        
        Args:
            criteria: Search criteria (e.g., "(Stage:equals:Qualification)")
            fields: Fields to retrieve
            max_records: Maximum records to fetch (safety limit)
            
        Returns:
            Combined results with all matching deals
        """
        all_deals = []
        page = 1
        per_page = 200  # Max allowed by Zoho
        
        while len(all_deals) < max_records:
            try:
                result = await self.search_deals(
                    criteria=criteria,
                    page=page,
                    per_page=per_page,
                    fields=fields,
                )
                
                deals = result.get("data", [])
                if not deals:
                    break
                    
                all_deals.extend(deals)
                logger.info(f"Fetched page {page}: {len(deals)} deals (total: {len(all_deals)})")
                
                # Check if there are more records
                info = result.get("info", {})
                if not info.get("more_records", False):
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total deals fetched: {len(all_deals)}")
        
        return {
            "data": all_deals,
            "info": {
                "count": len(all_deals),
                "page": 1,
                "per_page": len(all_deals),
                "more_records": False,
            }
        }
    
    async def get_deal_attachments(self, deal_id: str) -> List[Dict[str, Any]]:
        """
        Get list of attachments for a deal.
        
        Args:
            deal_id: Zoho Deal ID
            
        Returns:
            List of attachment metadata (id, file_name, size, etc.)
        """
        try:
            params = {
                "fields": ",".join(self.DEFAULT_ATTACHMENT_FIELDS)
            }
            result = await self._make_request(
                "GET", 
                f"/Deals/{deal_id}/Attachments",
                params=params
            )
            return result.get("data", [])
        except Exception as e:
            logger.warning(f"Error fetching attachments for deal {deal_id}: {e}")
            return []
    
    async def download_deal_attachment(self, deal_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download an attachment file content from a deal.
        
        Args:
            deal_id: Zoho Deal ID
            attachment_id: Attachment ID
            
        Returns:
            File content as bytes, or None if failed
        """
        try:
            client = await self._get_client()
            headers = await self._get_headers()
            # Remove Content-Type for download
            headers.pop("Content-Type", None)
            
            url = f"{self._get_base_url()}/Deals/{deal_id}/Attachments/{attachment_id}"
            
            logger.info(f"[Zoho] >>> GET /Deals/{deal_id}/Attachments/{attachment_id} (download)")
            response = await client.get(url, headers=headers)
            logger.info(f"[Zoho] <<< GET /Deals/{deal_id}/Attachments/{attachment_id} — status: {response.status_code}, size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"[Zoho] Failed to download deal attachment {attachment_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[Zoho] Error downloading deal attachment {attachment_id}: {e}")
            return None
    
    async def get_deal_attachments_with_content(
        self, 
        deal_id: str,
        supported_extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a deal with their file content.
        
        Args:
            deal_id: Zoho Deal ID
            supported_extensions: List of file extensions to download (e.g., ['.pdf', '.docx'])
                                 If None, downloads common document types.
            
        Returns:
            List of attachment dicts with 'content' key containing bytes
        """
        if supported_extensions is None:
            supported_extensions = [
                '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                '.txt', '.rtf', '.xls', '.xlsx'
            ]
        
        attachments = await self.get_deal_attachments(deal_id)
        
        result = []
        for attachment in attachments:
            file_name = attachment.get("File_Name", "")
            attachment_id = attachment.get("id")
            
            if not attachment_id:
                continue
            
            # Check if file extension is supported
            ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""
            if ext not in supported_extensions:
                logger.debug(f"Skipping unsupported file type: {file_name}")
                continue
            
            # Download the content
            content = await self.download_deal_attachment(deal_id, attachment_id)
            
            if content:
                result.append({
                    "id": attachment_id,
                    "file_name": file_name,
                    "extension": ext,
                    "size": attachment.get("Size", len(content)),
                    "content": content,
                    "created_time": attachment.get("Created_Time"),
                })
                logger.info(f"Downloaded deal attachment: {file_name} ({len(content)} bytes)")
            else:
                logger.warning(f"Failed to download deal attachment: {file_name}")
        
        return result
    
    # ==================== GENERIC MODULE OPERATIONS ====================
    
    async def get_records(
        self,
        module: str,
        page: int = 1,
        per_page: int = 200,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get records from any Zoho CRM module.
        
        Args:
            module: Module name (e.g., "Leads", "Contacts", "Accounts")
            page: Page number
            per_page: Records per page
            fields: Fields to retrieve (required in v7 - will use module defaults if not provided)
            
        Returns:
            Module records
        """
        # Get default fields based on module name (required in Zoho CRM API v7)
        if fields:
            field_list = fields
        elif module.lower() == "leads":
            field_list = self.DEFAULT_LEAD_FIELDS
        elif module.lower() == "contacts":
            field_list = self.DEFAULT_CONTACT_FIELDS
        elif module.lower() == "deals":
            field_list = self.DEFAULT_DEAL_FIELDS
        else:
            # For other modules, use basic fields
            field_list = ["id", "Created_Time", "Modified_Time", "Owner"]
        
        params = {
            "fields": ",".join(field_list),
            "page": page,
            "per_page": min(per_page, 200),
        }
        return await self._make_request("GET", f"/{module}", params=params)


# Create service instance
zoho_crm_service = ZohoCRMService()
