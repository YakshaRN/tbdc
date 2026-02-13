"""
Deal Analysis Service for the Application Module.

Provides AI-powered analysis of deal data including:
- Company identification
- Revenue from Top 5 Customers
- ICP Mapping for Canada
- Scoring Rubric and Fit Assessment
- Support Required from TBDC
"""
import json
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.llm.bedrock_service import bedrock_service
from app.schemas.deal_analysis import DealAnalysis, RevenueCustomer, PricingSummary, PricingLineItem


# TBDC Service Pricing Catalog - used by LLM to recommend services
TBDC_PRICING_CATALOG = {
    "core_services": [
        {
            "name": "Scout Report",
            "description": "Comprehensive market analysis",
            "unit_price_eur": 4000,
        },
        {
            "name": "Mentor Hours (x4 hours)",
            "description": "Base mentorship sessions",
            "unit_price_eur": 2000,
        },
        {
            "name": "Startup Ecosystem Events",
            "description": "Access to startup events",
            "unit_price_eur": 0,
        },
        {
            "name": "Investor & Regulatory Sessions",
            "description": "Sessions with IP lawyer",
            "unit_price_eur": 0,
        },
        {
            "name": "Office Access & Meeting Rooms",
            "description": "Workspace and facilities",
            "unit_price_eur": 0,
        },
        {
            "name": "$500k Tech Credits",
            "description": "Technology platform credits",
            "unit_price_eur": 0,
        },
    ],
    "customer_meetings": {
        "enterprise_meetings": {
            "description": "High-value customer engagement sessions",
            "unit_price_eur": 2000,
            "default": 1,
        },
        "smb_meetings": {
            "description": "SMB customer engagement sessions",
            "unit_price_eur": 1500,
            "default": 3,
        },
    },
    "investor_meetings": {
        "category_a": {
            "description": "High-value investor introduction sessions",
            "unit_price_eur": 2500,
        },
        "category_b": {
            "description": "Investor introduction sessions",
            "unit_price_eur": 1500,
        },
    },
    "additional_services": [
        {
            "name": "Deal Memo",
            "description": "Professional deal documentation",
            "unit_price_eur": 2000,
        },
    ],
}


# Prompts are loaded from prompt_manager (DynamoDB only).

class DealAnalysisService:
    """
    Service for analyzing deals using LLM.
    All prompts are fetched from DynamoDB via prompt_manager on every call (no cache).
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def _get_prompt_manager(self):
        """Lazy import to avoid circular imports."""
        from app.services.llm.prompt_manager import prompt_manager
        return prompt_manager
    
    def get_system_prompt(self) -> str:
        """Get the deal system prompt from DynamoDB."""
        return self._get_prompt_manager().get_deal_system_prompt()
    
    def get_analysis_prompt(self) -> str:
        """Get the deal analysis prompt template from DynamoDB."""
        return self._get_prompt_manager().get_deal_analysis_prompt()
    
    def get_scoring_system_prompt(self) -> str:
        """Get the deal scoring system prompt from DynamoDB."""
        return self._get_prompt_manager().get_deal_scoring_system_prompt()
    
    def get_scoring_prompt(self) -> str:
        """Get the deal scoring prompt template from DynamoDB."""
        return self._get_prompt_manager().get_deal_scoring_prompt()
    
    def analyze_deal(
        self, 
        deal_data: Dict[str, Any],
        attachment_text: Optional[str] = None,
        meeting_text: Optional[str] = None
    ) -> DealAnalysis:
        """
        Analyze deal data using LLM and return structured insights.
        
        Makes two separate LLM calls:
        1. Main analysis - company info, ICP, pricing, support, etc.
        2. Scoring rubric - dedicated scoring with detailed criteria
        
        Args:
            deal_data: Deal data from Zoho CRM
            attachment_text: Optional extracted text from deal attachments 
                            (pitch decks, PDFs, documents, etc.)
            meeting_text: Optional meeting notes from Fireflies.ai
            
        Returns:
            DealAnalysis object with AI-generated insights
        """
        # Format deal data for the prompt
        formatted_data = self._format_deal_data(deal_data, attachment_text, meeting_text)
        
        # ---- LLM Call 1: Main deal analysis ----
        logger.info("[DealAnalysis] LLM Call 1/2: Sending main deal analysis request to Bedrock")
        analysis_data = self._run_main_analysis(formatted_data, attachment_text)
        logger.info(f"[DealAnalysis] LLM Call 1/2 done: Got {len(analysis_data)} fields from main analysis")
        logger.info("[DealAnalysis] LLM Call 1/2 fields received:\n" + "\n".join(f"  {k}: {v}" for k, v in analysis_data.items()))
        
        # Convert revenue_top_5_customers to proper format
        if "revenue_top_5_customers" in analysis_data:
            analysis_data["revenue_top_5_customers"] = [
                RevenueCustomer(**customer) if isinstance(customer, dict) else customer
                for customer in analysis_data["revenue_top_5_customers"]
            ]
        
        # Convert pricing_summary to proper format
        if "pricing_summary" in analysis_data and isinstance(analysis_data["pricing_summary"], dict):
            pricing_data = analysis_data["pricing_summary"]
            if "recommended_services" in pricing_data:
                pricing_data["recommended_services"] = [
                    PricingLineItem(**item) if isinstance(item, dict) else item
                    for item in pricing_data["recommended_services"]
                ]
            # Recalculate total to ensure accuracy
            pricing_data["total_cost_eur"] = sum(
                item.total_price_eur if isinstance(item, PricingLineItem) else item.get("total_price_eur", 0)
                for item in pricing_data.get("recommended_services", [])
            )
            analysis_data["pricing_summary"] = PricingSummary(**pricing_data)
        
        # ---- LLM Call 2: Scoring rubric (separate, focused call) ----
        logger.info("[DealAnalysis] LLM Call 2/2: Sending scoring rubric request to Bedrock")
        scoring_data = self._run_scoring_rubric(formatted_data, analysis_data)
        logger.info(f"[DealAnalysis] LLM Call 2/2 done: fit_score={scoring_data.get('fit_score', 'N/A')}")
        
        # Merge scoring into analysis
        analysis_data["scoring_rubric"] = scoring_data.get("scoring_rubric", {
            "product_market_fit": 5,
            "canada_market_readiness": 5,
            "gtm_clarity": 5,
            "team_capability": 5,
            "revenue_potential": 5,
        })
        analysis_data["fit_score"] = scoring_data.get("fit_score", 5)
        analysis_data["fit_assessment"] = scoring_data.get("fit_assessment", "")
        
        logger.info("Deal analysis completed successfully (analysis + scoring)")
        
        return DealAnalysis(**analysis_data)
    
    def _run_main_analysis(
        self,
        formatted_data: str,
        attachment_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the main deal analysis LLM call (everything except scoring rubric).
        """
        system_prompt = self.get_system_prompt()
        analysis_prompt_template = self.get_analysis_prompt()
        
        # Safely substitute {deal_data} without touching other braces (e.g. JSON examples in prompt)
        if "{deal_data}" in analysis_prompt_template:
            prompt = analysis_prompt_template.replace("{deal_data}", formatted_data)
        else:
            logger.warning("Deal analysis prompt missing {deal_data} placeholder, appending data")
            prompt = f"{analysis_prompt_template}\n\n{formatted_data}"
        
        if attachment_text:
            logger.debug(f"Analyzing deal with LLM (including {len(attachment_text)} chars from attachments)...")
        else:
            logger.debug("Analyzing deal with LLM...")
        
        logger.info("=== DEAL ANALYSIS PROMPT START ===")
        logger.info(f"System Prompt ({len(system_prompt)} chars):\n{system_prompt}")
        logger.info(f"User Prompt ({len(prompt)} chars):\n{prompt}")
        logger.info("=== DEAL ANALYSIS PROMPT END ===")
        
        try:
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=8192,
                temperature=0.3,
            )
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error in main deal analysis: {e}")
            return self._get_default_analysis_data(str(e))
    
    def _run_scoring_rubric(
        self,
        formatted_data: str,
        analysis_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run a separate LLM call to generate the scoring rubric.
        
        Uses the deal data + preliminary analysis as context for more
        accurate and focused scoring.
        
        Args:
            formatted_data: Formatted deal data string
            analysis_data: Results from the main analysis (used as context)
            
        Returns:
            Dict with scoring_rubric, fit_score, and fit_assessment
        """
        # Build a concise analysis summary for the scoring LLM
        analysis_summary = self._build_analysis_summary(analysis_data)
        
        scoring_system_prompt = self.get_scoring_system_prompt()
        scoring_prompt_template = self.get_scoring_prompt()
        
        # Safely substitute placeholders without touching other braces (e.g. JSON examples in prompt)
        prompt = scoring_prompt_template
        if "{deal_data}" in prompt:
            prompt = prompt.replace("{deal_data}", formatted_data)
        else:
            logger.warning("Scoring prompt missing {deal_data} placeholder, appending data")
            prompt = f"{prompt}\n\nDeal Information:\n{formatted_data}"
        if "{analysis_summary}" in prompt:
            prompt = prompt.replace("{analysis_summary}", analysis_summary)
        else:
            logger.warning("Scoring prompt missing {analysis_summary} placeholder, appending summary")
            prompt = f"{prompt}\n\nAnalysis:\n{analysis_summary}"
        
        logger.info("=== SCORING RUBRIC PROMPT START ===")
        logger.info(f"System Prompt ({len(scoring_system_prompt)} chars):\n{scoring_system_prompt}")
        logger.info(f"User Prompt ({len(prompt)} chars):\n{prompt}")
        logger.info("=== SCORING RUBRIC PROMPT END ===")
        
        try:
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt=scoring_system_prompt,
                max_tokens=1024,  # Scoring response is small
                temperature=0.2,  # Lower temperature for consistent scoring
            )
            
            scoring_data = self._parse_response(response)
            
            # Validate the response has expected fields
            if "scoring_rubric" not in scoring_data or "fit_score" not in scoring_data:
                logger.warning("Scoring LLM response missing expected fields, using defaults")
                return self._get_default_scoring_data()
            
            logger.info(
                f"Scoring rubric generated: fit_score={scoring_data.get('fit_score')}, "
                f"rubric={scoring_data.get('scoring_rubric')}"
            )
            return scoring_data
            
        except Exception as e:
            logger.error(f"Error generating scoring rubric: {e}")
            return self._get_default_scoring_data()
    
    def _build_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """
        Build a concise summary of the main analysis to provide context
        for the scoring rubric LLM call.
        """
        lines = []
        
        field_map = {
            "company_name": "Company",
            "country": "Country",
            "region": "Region",
            "summary": "Summary",
            "product_description": "Product",
            "vertical": "Vertical",
            "business_model": "Business Model",
            "motion": "GTM Motion",
            "raise_stage": "Funding Stage",
            "company_size": "Company Size",
            "likely_icp_canada": "Likely ICP Canada",
            "icp_mapping": "ICP Mapping",
            "support_required": "Support Required",
        }
        
        for key, label in field_map.items():
            value = analysis_data.get(key)
            if value and value != "Unknown" and value != "":
                # Handle Pydantic model objects
                if hasattr(value, "model_dump"):
                    value = str(value.model_dump())
                lines.append(f"- {label}: {value}")
        
        # Include key insights
        insights = analysis_data.get("key_insights", [])
        if insights:
            lines.append(f"- Key Insights: {'; '.join(insights[:3])}")
        
        # Include support recommendations
        recs = analysis_data.get("support_recommendations", [])
        if recs:
            lines.append(f"- Support Recommendations: {'; '.join(recs[:3])}")
        
        # Include top customers summary
        customers = analysis_data.get("revenue_top_5_customers", [])
        if customers:
            customer_names = []
            for c in customers[:3]:
                if isinstance(c, dict):
                    customer_names.append(c.get("name", "Unknown"))
                elif hasattr(c, "name"):
                    customer_names.append(c.name)
            if customer_names:
                lines.append(f"- Top Customers: {', '.join(customer_names)}")
        
        return "\n".join(lines) if lines else "No analysis data available"
    
    def _get_default_scoring_data(self) -> Dict[str, Any]:
        """Return default scoring data when scoring LLM call fails."""
        return {
            "scoring_rubric": {
                "product_market_fit": 5,
                "canada_market_readiness": 5,
                "gtm_clarity": 5,
                "team_capability": 5,
                "revenue_potential": 5,
            },
            "fit_score": 5,
            "fit_assessment": "Scoring unavailable - manual assessment recommended",
        }
    
    def _format_deal_data(
        self, 
        deal_data: Dict[str, Any],
        attachment_text: Optional[str] = None,
        meeting_text: Optional[str] = None
    ) -> str:
        """
        Format deal data as readable text for the LLM.
        
        Args:
            deal_data: Deal data from Zoho CRM
            attachment_text: Optional extracted text from attachments
            meeting_text: Optional meeting notes from Fireflies.ai
            
        Returns:
            Formatted string for LLM prompt
        """
        formatted_lines = []
        
        # Priority fields to include for deals
        priority_fields = [
            "Deal_Name", "Account_Name", "Contact_Name", "Amount",
            "Stage", "Closing_Date", "Probability", "Type", "Lead_Source",
            "Industry", "Company_Website", "Website", "Description",
            "Support_Required", "Country", "Created_Time", "Modified_Time",
            # Revenue fields (for LLM reformatting)
            "Projected_company_revenue_in_current_fisca",
            "Sales_revenue_since_being_incorporated",
            "Company_revenue_in_current_fiscal_year_CAD",
            "Company_Monthly_Revenue",
            "Revenue_Range",
            "Company_revenue_in_last_fiscal_year_CAD",
            # Customer fields (for LLM reformatting)
            "Top_5_Customers",
            "Target_Markets_or_Customer_Segments",
            "Target_Customer_Type",
            "Customer_Example",
            # Support & ICP (for LLM reformatting)
            "Specific_Area_of_Support_Required",
        ]
        
        for field in priority_fields:
            if field in deal_data and deal_data[field]:
                value = deal_data[field]
                # Handle nested objects (like Account_Name which may be {id, name})
                if isinstance(value, dict):
                    if "name" in value:
                        value = value["name"]
                    else:
                        value = str(value)
                formatted_lines.append(f"- {field.replace('_', ' ')}: {value}")
        
        # Add any other non-empty fields
        for key, value in deal_data.items():
            if key not in priority_fields and value and key != "id":
                if not key.startswith("$") and not key.startswith("_"):
                    # Handle nested objects
                    if isinstance(value, dict):
                        if "name" in value:
                            value = value["name"]
                        else:
                            continue  # Skip complex nested objects
                    formatted_lines.append(f"- {key.replace('_', ' ')}: {value}")
        
        result = "\n".join(formatted_lines) if formatted_lines else "No deal data available"
        
        # Add attachment content if available
        if attachment_text and attachment_text.strip():
            result += "\n\n=== ATTACHED DOCUMENTS (Pitch Deck / PDF / Slides) ===\n"
            result += attachment_text
            result += "\n=== END OF ATTACHED DOCUMENTS ==="
        
        # Add Fireflies meeting notes if available
        if meeting_text and meeting_text.strip():
            result += "\n\n=== MEETING NOTES (Fireflies.ai) ===\n"
            result += meeting_text
            result += "\n=== END OF MEETING NOTES ==="
        
        return result
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON, handling truncation gracefully."""
        # Step 1: Try to parse directly
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Step 2: Try to extract JSON from response text
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Step 3: Handle truncated JSON - try to close open braces/brackets
        try:
            start = response.find("{")
            if start != -1:
                json_text = response[start:]
                # Count open vs close braces and brackets
                repaired = self._repair_truncated_json(json_text)
                if repaired:
                    result = json.loads(repaired)
                    logger.warning("Parsed truncated JSON response after repair (some fields may be missing)")
                    return result
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"JSON repair attempt failed: {e}")
        
        logger.warning("Failed to parse LLM response as JSON")
        return self._get_default_analysis_data("Failed to parse LLM response")
    
    def _repair_truncated_json(self, json_text: str) -> Optional[str]:
        """
        Attempt to repair truncated JSON by closing open structures.
        Handles cases where LLM response was cut off by max_tokens.
        """
        # Remove any trailing incomplete string value
        # Find the last complete key-value pair
        text = json_text.rstrip()
        
        # Track open brackets and braces
        stack = []
        in_string = False
        escape_next = False
        last_valid_pos = 0
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char in ('{', '['):
                stack.append(char)
                last_valid_pos = i
            elif char == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
                    last_valid_pos = i
            elif char == ']':
                if stack and stack[-1] == '[':
                    stack.pop()
                    last_valid_pos = i
        
        if not stack:
            # JSON is already balanced
            return text
        
        # Truncate to last complete value by finding last comma, closing bracket, or value end
        # Then close remaining open structures
        truncated = text
        
        # If we're inside a string, close it
        if in_string:
            truncated += '"'
        
        # Close remaining open structures in reverse order
        for opener in reversed(stack):
            if opener == '{':
                # Remove any trailing comma or incomplete key
                truncated = truncated.rstrip()
                if truncated.endswith(','):
                    truncated = truncated[:-1]
                # Remove incomplete key-value pairs (e.g., trailing "key":)
                if truncated.endswith(':'):
                    # Remove the incomplete key
                    last_quote = truncated.rfind('"', 0, len(truncated) - 1)
                    if last_quote > 0:
                        second_last_quote = truncated.rfind('"', 0, last_quote)
                        if second_last_quote >= 0:
                            truncated = truncated[:second_last_quote].rstrip().rstrip(',')
                truncated += '}'
            elif opener == '[':
                truncated = truncated.rstrip()
                if truncated.endswith(','):
                    truncated = truncated[:-1]
                truncated += ']'
        
        return truncated
    
    def _get_default_analysis_data(self, error_message: str) -> Dict[str, Any]:
        """Return default analysis data when LLM fails."""
        return {
            "company_name": "Unknown",
            "country": "Unknown",
            "region": "Unknown",
            "summary": "Unable to determine from available data",
            "product_description": "Unable to determine from available data",
            "vertical": "Unknown",
            "business_model": "Unknown",
            "motion": "Unknown",
            "raise_stage": "Unknown",
            "company_size": "Unknown",
            "revenue_top_5_customers": [],
            "scoring_rubric": {
                "product_market_fit": 5,
                "canada_market_readiness": 5,
                "gtm_clarity": 5,
                "team_capability": 5,
                "revenue_potential": 5
            },
            "fit_score": 5,
            "fit_assessment": f"Analysis unavailable: {error_message}",
            "icp_mapping": "Unknown",
            "likely_icp_canada": "Unknown",
            "support_required": "Manual review required",
            "support_recommendations": ["Manual assessment needed due to analysis failure"],
            "pricing_summary": None,
            "key_insights": ["Analysis could not be completed - manual review required"],
            "questions_to_ask": [
                "What is your core product and who is your primary customer?",
                "Have you explored the Canadian market before?",
                "What is your current GTM motion?",
                "What stage of funding are you at?",
                "What would success in Canada look like for you?",
            ],
            "confidence_level": "Low",
            "notes": [f"Automated analysis failed: {error_message}"],
        }
    
    def _get_default_analysis(self, error_message: str) -> DealAnalysis:
        """Return default DealAnalysis object when LLM fails."""
        return DealAnalysis(**self._get_default_analysis_data(error_message))


# Create singleton instance
deal_analysis_service = DealAnalysisService()
