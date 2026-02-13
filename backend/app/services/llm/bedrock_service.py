"""
AWS Bedrock LLM Service for Lead Analysis.

Provides AI-powered analysis of lead data including:
- Country identification
- Funding stage (Raise)
- Industry vertical
- Business model classification
- Fit assessment
- Suggested questions to ask
"""
import json
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings
from app.schemas.lead_analysis import LeadAnalysis


class BedrockService:
    """
    AWS Bedrock service for invoking foundation models.
    """
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        """Get or create Bedrock runtime client."""
        if self._client is None:
            # If explicit credentials are provided, use them
            # Otherwise, boto3 will use IAM role credentials automatically
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            else:
                # Use default credential chain (IAM role, env vars, etc.)
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                )
        return self._client
    
    @property
    def is_configured(self) -> bool:
        """Check if Bedrock is available (via credentials or IAM role)."""
        # Cache the result after first check
        if hasattr(self, '_is_configured_cached'):
            return self._is_configured_cached
        
        try:
            # Try to get client - this will use IAM role if no explicit credentials
            client = self._get_client()
            # Verify we can actually use the service by listing a model
            # This is a lightweight call just to check access
            self._is_configured_cached = True
            logger.info("Bedrock service configured and available")
            return True
        except Exception as e:
            logger.warning(f"Bedrock not available: {e}")
            self._is_configured_cached = False
            return False
    
    def invoke_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> str:
        """
        Invoke Claude model on AWS Bedrock.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Model response text
        """
        client = self._get_client()
        
        max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
        temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
        
        # Build request body for Claude models
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        try:
            response = client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from Claude response
            if "content" in response_body and len(response_body["content"]) > 0:
                response_text = response_body["content"][0]["text"]
                
                # Check for truncation via stop_reason
                stop_reason = response_body.get("stop_reason", "unknown")
                if stop_reason == "max_tokens":
                    logger.warning(
                        f"LLM response was TRUNCATED (stop_reason=max_tokens). "
                        f"Increase max_tokens to get complete output. "
                        f"Current response length: {len(response_text)} chars"
                    )
                
                # Log the full LLM response
                logger.info(f"=== LLM RESPONSE START ===")
                logger.info(f"Model: {settings.BEDROCK_MODEL_ID}")
                logger.info(f"Stop reason: {stop_reason}")
                logger.info(f"Response length: {len(response_text)} chars")
                logger.info(f"Response:\n{response_text}")
                logger.info(f"=== LLM RESPONSE END ===")
                
                # Also log token usage if available
                if "usage" in response_body:
                    usage = response_body["usage"]
                    logger.info(f"Token usage - Input: {usage.get('input_tokens', 'N/A')}, Output: {usage.get('output_tokens', 'N/A')}")
                
                return response_text
            
            logger.warning("Empty response from LLM")
            return ""
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error invoking Bedrock: {e}")
            raise


class LeadAnalysisService:
    """
    Service for analyzing leads using LLM.
    """
    
    SYSTEM_PROMPT = """You are an expert B2B lead qualification specialist.

Your role is to evaluate global startups for Canada and/or North America fit.
You assess the company's product, business model, GTM motion, funding maturity, and suitability
for entering the Canadian market.

## Output Purpose
Your output is used by strategy and sales teams to:
- Decide whether the company is worth outreach
- Prioritize leads for programs
- Identify key Canada-specific GTM considerations

## Evaluation Rules
- Always review the company's official website first (homepage, product, solutions, or industries pages).
- Use 2-3 max third-party sources to cross-check information/reviews about the company.
- If the website is vague or unclear, you must explicitly state this and lower your confidence.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.
- Never invent product features or use cases.

## Response Format
Always respond with valid JSON only using this exact structure:

{
  "company_name": "Company name or primary domain",
  "country": "Country where the company is based",
  "region": "Geographic region (e.g., North America, Europe, APAC)",
  "summary": "Summary about company and its potential",
  "product_description": "One-line description or 'Unclear from site'",
  "vertical": "Industry vertical (e.g., Fintech, Healthtech, SaaS)",
  "business_model": "B2B, B2C, B2B2C, Marketplace, Subscription, Services-led",
  "motion": "SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy",
  "raise_stage": "Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown",
  "company_size": "Startup, SMB, Mid-Market, Enterprise, Unknown",
  "likely_icp_canada": "Most likely Canadian customer profile",
  "fit_score": 1-10,
  "fit_assessment": "Brief assessment of Canada fit",
  "key_insights": ["3-5 concise insights"],
  "questions_to_ask": ["5-7 strategic questions"],
  "confidence_level": "High, Medium, or Low",
  "notes": ["Important caveats"]
}

Do not include explanations, markdown, or any text outside the JSON object."""


    ANALYSIS_PROMPT_TEMPLATE = """Evaluate the following company for Canada fit.

Company Input:
{lead_data}"""


    def __init__(self, bedrock_service: BedrockService):
        self.bedrock = bedrock_service
        # Import here to avoid circular imports
        from app.services.llm.prompt_manager import prompt_manager
        self.prompt_manager = prompt_manager
    
    def analyze_lead(
        self, 
        lead_data: Dict[str, Any],
        attachment_text: Optional[str] = None,
        website_text: Optional[str] = None,
        linkedin_text: Optional[str] = None,
    ) -> LeadAnalysis:
        """
        Analyze lead data using LLM and return structured insights.
        
        Args:
            lead_data: Lead data from Zoho CRM
            attachment_text: Optional extracted text from lead attachments 
                            (pitch decks, PDFs, documents, etc.)
            website_text: Optional scraped plain-text from the company website
            linkedin_text: Optional scraped plain-text from the LinkedIn profile
            
        Returns:
            LeadAnalysis object with AI-generated insights
        """
        # Format lead data for the prompt
        formatted_data = self._format_lead_data(
            lead_data, attachment_text, website_text, linkedin_text
        )
        
        # Get prompts from prompt manager (allows runtime updates)
        analysis_prompt_template = self.prompt_manager.get_analysis_prompt()
        system_prompt = self.prompt_manager.get_system_prompt()
        
        # Safely substitute {lead_data} without touching other braces (e.g. JSON examples in prompt)
        if "{lead_data}" in analysis_prompt_template:
            prompt = analysis_prompt_template.replace("{lead_data}", formatted_data)
        else:
            logger.warning("Analysis prompt missing {lead_data} placeholder, appending data")
            prompt = f"{analysis_prompt_template}\n\n{formatted_data}"
        
        if attachment_text:
            logger.debug(f"Analyzing lead with LLM (including {len(attachment_text)} chars from attachments)...")
        else:
            logger.debug(f"Analyzing lead with LLM...")
        
        # Log the final prompt being sent to LLM
        logger.info("=== LEAD ANALYSIS PROMPT START ===")
        logger.info(f"System Prompt ({len(system_prompt)} chars):\n{system_prompt[:500]}...")
        logger.info(f"User Prompt ({len(prompt)} chars):\n{prompt}")
        logger.info("=== LEAD ANALYSIS PROMPT END ===")
        
        try:
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            # Parse JSON response
            analysis_data = self._parse_response(response)
            
            logger.info(f"Lead analysis completed successfully")
            
            return LeadAnalysis(**analysis_data)
            
        except Exception as e:
            logger.error(f"Error analyzing lead: {e}")
            # Return default analysis on error
            return self._get_default_analysis(str(e))
    
    def _format_lead_data(
        self, 
        lead_data: Dict[str, Any],
        attachment_text: Optional[str] = None,
        website_text: Optional[str] = None,
        linkedin_text: Optional[str] = None,
    ) -> str:
        """
        Format lead data as readable text for the LLM.
        
        Args:
            lead_data: Lead data from Zoho CRM
            attachment_text: Optional extracted text from attachments
            website_text: Optional scraped plain-text from the company website
            linkedin_text: Optional scraped plain-text from the LinkedIn profile
            
        Returns:
            Formatted string for LLM prompt
        """
        # Filter out None values and format nicely
        formatted_lines = []
        
        # Priority fields to include
        priority_fields = [
            "First_Name", "Last_Name", "Email", "Phone", "Mobile",
            "Company", "Title", "Industry", "Lead_Source", "Lead_Status",
            "Website", "LinkedIn_Profile", "Description", "Street", "City",
            "State", "Zip_Code", "Country", "Annual_Revenue", "No_of_Employees",
        ]
        
        for field in priority_fields:
            if field in lead_data and lead_data[field]:
                formatted_lines.append(f"- {field.replace('_', ' ')}: {lead_data[field]}")
        
        # Add any other non-empty fields
        for key, value in lead_data.items():
            if key not in priority_fields and value and key != "id":
                if not key.startswith("$") and not key.startswith("_"):
                    formatted_lines.append(f"- {key.replace('_', ' ')}: {value}")
        
        result = "\n".join(formatted_lines) if formatted_lines else "No lead data available"
        
        # Add attachment content if available
        if attachment_text and attachment_text.strip():
            result += "\n\n=== ATTACHED DOCUMENTS (Pitch Deck / PDF / Slides) ===\n"
            result += attachment_text
            result += "\n=== END OF ATTACHED DOCUMENTS ==="
        
        # Add scraped website content if available
        if website_text and website_text.strip():
            result += "\n\n=== SCRAPED WEBSITE CONTENT ===\n"
            result += website_text
            result += "\n=== END OF SCRAPED WEBSITE CONTENT ==="
        
        # Add scraped LinkedIn profile content if available
        if linkedin_text and linkedin_text.strip():
            result += "\n\n=== SCRAPED LINKEDIN PROFILE ===\n"
            result += linkedin_text
            result += "\n=== END OF SCRAPED LINKEDIN PROFILE ==="

        
        logger.info(f"****** Formatted lead data: {result} ******")
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
            "likely_icp_canada": "Unknown",
            "fit_score": 5,
            "fit_assessment": f"Analysis unavailable: {error_message}",
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
    
    def _get_default_analysis(self, error_message: str) -> LeadAnalysis:
        """Return default LeadAnalysis object when LLM fails."""
        return LeadAnalysis(**self._get_default_analysis_data(error_message))


# Create singleton instances
bedrock_service = BedrockService()
lead_analysis_service = LeadAnalysisService(bedrock_service)
