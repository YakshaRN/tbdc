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
from app.schemas.deal_analysis import DealAnalysis, RevenueCustomer


# Default prompts for deal analysis
DEFAULT_DEAL_SYSTEM_PROMPT = """You are an expert B2B deal qualification and application assessment specialist.

Your role is to evaluate companies in the application pipeline for Canada and/or North America fit.
You assess the company's product, business model, GTM motion, funding maturity, revenue potential,
and suitability for TBDC support in entering the Canadian market.

## Output Purpose
Your output is used by strategy and business development teams to:
- Evaluate application fit for TBDC programs
- Identify top revenue-generating customer profiles
- Map the Ideal Customer Profile (ICP) for Canada
- Determine what support the company needs from TBDC
- Create a scoring rubric for prioritization

## Evaluation Rules
- Always review the company's official website first (homepage, product, solutions, or industries pages).
- Use the deal information and any attached documents to understand the company.
- If the website is vague or unclear, you must explicitly state this and lower your confidence.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.
- Never invent product features or use cases.
- Focus on Canada market entry potential and support requirements.

## Response Format
Always respond with valid JSON only using this exact structure:

{
  "company_name": "Company name",
  "country": "Country where the company is based",
  "region": "Geographic region (e.g., North America, Europe, APAC)",
  "summary": "Summary about company and its potential for Canada market entry",
  "product_description": "One-line description or 'Unclear from available data'",
  "vertical": "Industry vertical (e.g., Fintech, Healthtech, SaaS, Logistics, Data/AI)",
  "business_model": "B2B, B2C, B2B2C, Marketplace, Subscription, Services-led",
  "motion": "SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy",
  "raise_stage": "Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown",
  "company_size": "Startup, SMB, Mid-Market, Enterprise, Unknown",
  "revenue_top_5_customers": [
    {
      "name": "Customer/company name or type",
      "industry": "Customer industry",
      "revenue_contribution": "Significance (e.g., Major, Significant, Growing)",
      "description": "Brief description of the customer relationship"
    }
  ],
  "scoring_rubric": {
    "product_market_fit": 1-10,
    "canada_market_readiness": 1-10,
    "gtm_clarity": 1-10,
    "team_capability": 1-10,
    "revenue_potential": 1-10
  },
  "fit_score": 1-10,
  "fit_assessment": "Brief assessment of Canada fit and TBDC program suitability",
  "icp_mapping": "Detailed Ideal Customer Profile for Canada market",
  "likely_icp_canada": "Most likely Canadian customer profile (e.g., SMBs, mid-market enterprises, regulated industries)",
  "support_required": "What support does this company need from TBDC?",
  "support_recommendations": ["List of specific support actions TBDC can provide"],
  "key_insights": ["3-5 concise insights about the company and Canada opportunity"],
  "questions_to_ask": ["5-7 strategic questions to validate Canada entry, ICP, and GTM feasibility"],
  "confidence_level": "High, Medium, or Low",
  "notes": ["Important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product"]
}

Do not include explanations, markdown, or any text outside the JSON object."""


DEFAULT_DEAL_ANALYSIS_PROMPT = """Evaluate the following application/deal for Canada market fit and TBDC program suitability.

Deal Information:
{deal_data}"""


class DealAnalysisService:
    """
    Service for analyzing deals using LLM.
    Separate from LeadAnalysisService to handle deal-specific analysis.
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
        self._system_prompt = DEFAULT_DEAL_SYSTEM_PROMPT
        self._analysis_prompt_template = DEFAULT_DEAL_ANALYSIS_PROMPT
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt for deal analysis."""
        # You can extend this to load from prompt_manager or a separate config
        return self._system_prompt
    
    def get_analysis_prompt(self) -> str:
        """Get the current analysis prompt template for deals."""
        return self._analysis_prompt_template
    
    def update_prompts(
        self, 
        system_prompt: Optional[str] = None, 
        analysis_prompt: Optional[str] = None
    ) -> None:
        """Update the deal analysis prompts."""
        if system_prompt:
            self._system_prompt = system_prompt
        if analysis_prompt:
            self._analysis_prompt_template = analysis_prompt
    
    def analyze_deal(
        self, 
        deal_data: Dict[str, Any],
        attachment_text: Optional[str] = None
    ) -> DealAnalysis:
        """
        Analyze deal data using LLM and return structured insights.
        
        Args:
            deal_data: Deal data from Zoho CRM
            attachment_text: Optional extracted text from deal attachments 
                            (pitch decks, PDFs, documents, etc.)
            
        Returns:
            DealAnalysis object with AI-generated insights
        """
        # Format deal data for the prompt
        formatted_data = self._format_deal_data(deal_data, attachment_text)
        
        # Get prompts
        system_prompt = self.get_system_prompt()
        analysis_prompt_template = self.get_analysis_prompt()
        
        # Format the prompt
        try:
            prompt = analysis_prompt_template.format(deal_data=formatted_data)
        except KeyError as e:
            logger.warning(f"Prompt formatting error: {e}")
            prompt = f"Evaluate the following application/deal for Canada market fit:\n\n{formatted_data}"
        
        if attachment_text:
            logger.debug(f"Analyzing deal with LLM (including {len(attachment_text)} chars from attachments)...")
        else:
            logger.debug(f"Analyzing deal with LLM...")
        
        # Log the final prompt being sent to LLM
        logger.info("=== DEAL ANALYSIS PROMPT START ===")
        logger.info(f"System Prompt ({len(system_prompt)} chars):\n{system_prompt[:500]}...")
        logger.info(f"User Prompt ({len(prompt)} chars):\n{prompt}")
        logger.info("=== DEAL ANALYSIS PROMPT END ===")
        
        try:
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            # Parse JSON response
            analysis_data = self._parse_response(response)
            
            # Convert revenue_top_5_customers to proper format
            if "revenue_top_5_customers" in analysis_data:
                analysis_data["revenue_top_5_customers"] = [
                    RevenueCustomer(**customer) if isinstance(customer, dict) else customer
                    for customer in analysis_data["revenue_top_5_customers"]
                ]
            
            logger.info(f"Deal analysis completed successfully")
            
            return DealAnalysis(**analysis_data)
            
        except Exception as e:
            logger.error(f"Error analyzing deal: {e}")
            # Return default analysis on error
            return self._get_default_analysis(str(e))
    
    def _format_deal_data(
        self, 
        deal_data: Dict[str, Any],
        attachment_text: Optional[str] = None
    ) -> str:
        """
        Format deal data as readable text for the LLM.
        
        Args:
            deal_data: Deal data from Zoho CRM
            attachment_text: Optional extracted text from attachments
            
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
        
        return result
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        try:
            # Try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                # Find JSON object in response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
        
        logger.warning("Failed to parse LLM response as JSON")
        return self._get_default_analysis_data("Failed to parse LLM response")
    
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
