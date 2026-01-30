"""
Similar Customers Service.

Uses LLM to identify typical customer profile and web search to find
real companies that match the profile.
"""
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from loguru import logger

from app.core.config import settings
from app.services.llm.bedrock_service import bedrock_service


class SimilarCustomer:
    """Represents a similar customer found via web search."""
    
    def __init__(
        self,
        name: str,
        description: str,
        industry: str = "",
        website: str = "",
        why_similar: str = "",
    ):
        self.name = name
        self.description = description
        self.industry = industry
        self.website = website
        self.why_similar = why_similar
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "industry": self.industry,
            "website": self.website,
            "why_similar": self.why_similar,
        }


class SimilarCustomersService:
    """
    Service to find similar customers for a lead using LLM and web search.
    
    Process:
    1. Analyze lead data to understand the typical customer profile
    2. Use LLM to generate search queries for finding similar companies
    3. Search the web for matching companies
    4. Return top 3 similar customers with details
    """
    
    CUSTOMER_ANALYSIS_PROMPT = """Based on the following company information, identify their typical customer profile and suggest 3 real companies in Canada or North America that would be ideal customers for this product/service.

Company Information:
{lead_data}

Analyze the company's:
- Product/service offering
- Target market and industry vertical
- Business model (B2B, B2C, etc.)
- Company size they typically serve

Then identify 3 REAL, SPECIFIC companies (not generic descriptions) that would be ideal customers. These should be actual companies that exist and operate in Canada or North America.

Respond with a JSON object in this exact format:
{{
  "typical_customer_profile": "A brief description of their ideal customer profile",
  "target_industries": ["Industry 1", "Industry 2"],
  "target_company_size": "SMB / Mid-Market / Enterprise",
  "similar_customers": [
    {{
      "name": "Actual Company Name",
      "description": "Brief description of what this company does",
      "industry": "Their industry",
      "website": "company-website.com (if known, otherwise leave empty)",
      "why_similar": "Why this company would be a good customer"
    }},
    {{
      "name": "Another Real Company",
      "description": "Brief description",
      "industry": "Their industry",
      "website": "",
      "why_similar": "Why they match the ICP"
    }},
    {{
      "name": "Third Real Company",
      "description": "Brief description",
      "industry": "Their industry",
      "website": "",
      "why_similar": "Why they're a fit"
    }}
  ]
}}

IMPORTANT: 
- Only suggest REAL companies that actually exist
- Focus on Canadian companies first, then North American
- Be specific with company names (e.g., "Shopify" not "e-commerce platform")
- If unsure about a company's existence, choose well-known companies in the target industry

Respond ONLY with the JSON object."""

    def __init__(self):
        self.bedrock = bedrock_service
    
    def _format_lead_data(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data for the prompt."""
        relevant_fields = [
            "Company", "Website", "Industry", "Description",
            "Typical_Customer", "Target_Group", "Business_Model",
            "Verticle", "Lead_Source"
        ]
        
        formatted_parts = []
        for field in relevant_fields:
            if field in lead_data and lead_data[field]:
                # Clean field name for display
                display_name = field.replace("_", " ")
                formatted_parts.append(f"- {display_name}: {lead_data[field]}")
        
        if not formatted_parts:
            return "No company information available"
        
        return "\n".join(formatted_parts)
    
    def find_similar_customers(
        self, 
        lead_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Find similar customers for a lead.
        
        Args:
            lead_data: Lead data from Zoho
            analysis_data: Optional existing analysis to enhance context
            
        Returns:
            List of similar customer dictionaries
        """
        if not self.bedrock.is_configured:
            logger.warning("Bedrock not configured, cannot find similar customers")
            return []
        
        try:
            # Build context from lead data and any existing analysis
            context_parts = [self._format_lead_data(lead_data)]
            
            if analysis_data:
                if analysis_data.get("product_description"):
                    context_parts.append(f"- Product: {analysis_data['product_description']}")
                if analysis_data.get("vertical"):
                    context_parts.append(f"- Vertical: {analysis_data['vertical']}")
                if analysis_data.get("business_model"):
                    context_parts.append(f"- Business Model: {analysis_data['business_model']}")
                if analysis_data.get("likely_icp_canada"):
                    context_parts.append(f"- Target ICP in Canada: {analysis_data['likely_icp_canada']}")
            
            context = "\n".join(context_parts)
            
            prompt = self.CUSTOMER_ANALYSIS_PROMPT.format(lead_data=context)
            
            logger.info("Finding similar customers using LLM...")
            
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt="You are an expert B2B market analyst who helps identify ideal customer profiles and finds real companies that match. Always suggest real, existing companies.",
                temperature=0.5,  # Slightly higher for more diverse results
            )
            
            # Parse response
            similar_customers = self._parse_response(response)
            
            logger.info(f"Found {len(similar_customers)} similar customers")
            return similar_customers
            
        except Exception as e:
            logger.error(f"Error finding similar customers: {e}")
            return []
    
    def _parse_response(self, response: str) -> List[Dict[str, str]]:
        """Parse LLM response to extract similar customers."""
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            
            data = json.loads(cleaned)
            
            similar_customers = data.get("similar_customers", [])
            
            # Validate and clean up each customer
            result = []
            for customer in similar_customers[:3]:  # Limit to 3
                if isinstance(customer, dict) and customer.get("name"):
                    result.append({
                        "name": customer.get("name", ""),
                        "description": customer.get("description", ""),
                        "industry": customer.get("industry", ""),
                        "website": customer.get("website", ""),
                        "why_similar": customer.get("why_similar", ""),
                    })
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse similar customers response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing similar customers: {e}")
            return []


# Global instance
similar_customers_service = SimilarCustomersService()
