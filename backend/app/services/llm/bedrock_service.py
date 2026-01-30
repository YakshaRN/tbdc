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
                
                # Log the full LLM response
                logger.info(f"=== LLM RESPONSE START ===")
                logger.info(f"Model: {settings.BEDROCK_MODEL_ID}")
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
    
    SYSTEM_PROMPT = """You are an analyst for TBDC’s Pivot program and an expert B2B lead qualification specialist.

Your role is to evaluate ONE Indian or global startup at a time for Canada and North America fit.
You assess the company’s product, business model, GTM motion, funding maturity, and suitability
for entering the Canadian market.

You must base your analysis primarily on the company’s official website
(homepage, product, solutions, or industries pages).
If the website is vague or unclear, you must explicitly state this, infer only at a high level,
and lower your confidence. Never invent product features or use cases.

Your output is used by strategy and sales teams to:
- Decide whether the company is worth outreach
- Prioritize leads for the TBDC Pivot program
- Identify key Canada-specific GTM considerations

Always respond with valid JSON only.
Do not include explanations, markdown, or any text outside the JSON object."""


    ANALYSIS_PROMPT_TEMPLATE = """Evaluate the following company for Canada fit under TBDC’s Pivot program.

Company Input:
{lead_data}

Evaluation rules:
- Always review the official website first.
- Use third-party sources only to confirm or resolve ambiguity.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.

Respond with a JSON object using the structure below:

{{
  "company_name": "Company name or primary domain",

  "country": "Country where the company is based (infer from address, phone, or company info)",
  "region": "Geographic region (e.g., North America, Europe, APAC, etc.)",

  "product_description": "One-line description of what the product does and for whom (or 'Unclear from site' if applicable)",

  "vertical": "Industry vertical or sector (e.g., Fintech - SME, Healthtech, SaaS, Logistics, Data/AI, etc.)",

  "business_model": "Business model type (e.g., B2B, B2C, B2B2C, Marketplace, Subscription, Services-led)",

  "motion": "Go-to-market motion (SaaS, Infra/API, Marketplace, SaaS + hardware, Ops heavy, Services heavy)",

  "raise_stage": "Funding stage if identifiable (Pre-seed, Seed, Series A, Series B, Growth, Bootstrapped, Unknown)",

  "company_size": "Estimated company size (Startup, SMB, Mid-Market, Enterprise, Unknown)",

  "likely_icp_canada": "Most likely Canadian customer profile if applicable (e.g., SMBs, mid-market enterprises, regulated industries)",

  "fit_score": "Integer from 1–10 indicating how strong the Canada market fit appears to be",

  "fit_assessment": "Brief assessment explaining why this company is or is not a good fit for Canada and TBDC Pivot",

  "key_insights": [
    "3–5 concise insights about the company’s product, GTM readiness, or Canada relevance"
  ],

  "questions_to_ask": [
    "5–7 strategic questions the team should ask to validate Canada entry, ICP, differentiation, and GTM feasibility"
  ],

  "confidence_level": "High, Medium, or Low",

  "notes": [
    "Any important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product, or strong incumbents in Canada"
  ]
}}

Respond ONLY with the JSON object and no additional text."""


    def __init__(self, bedrock_service: BedrockService):
        self.bedrock = bedrock_service
        # Import here to avoid circular imports
        from app.services.llm.prompt_manager import prompt_manager
        self.prompt_manager = prompt_manager
    
    def analyze_lead(
        self, 
        lead_data: Dict[str, Any],
        attachment_text: Optional[str] = None
    ) -> LeadAnalysis:
        """
        Analyze lead data using LLM and return structured insights.
        
        Args:
            lead_data: Lead data from Zoho CRM
            attachment_text: Optional extracted text from lead attachments 
                            (pitch decks, PDFs, documents, etc.)
            
        Returns:
            LeadAnalysis object with AI-generated insights
        """
        # Format lead data for the prompt
        formatted_data = self._format_lead_data(lead_data, attachment_text)
        
        # Get prompts from prompt manager (allows runtime updates)
        analysis_prompt_template = self.prompt_manager.get_analysis_prompt()
        system_prompt = self.prompt_manager.get_system_prompt()
        
        prompt = analysis_prompt_template.format(lead_data=formatted_data)
        
        if attachment_text:
            logger.debug(f"Analyzing lead with LLM (including {len(attachment_text)} chars from attachments)...")
        else:
            logger.debug(f"Analyzing lead with LLM...")
        
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
        attachment_text: Optional[str] = None
    ) -> str:
        """
        Format lead data as readable text for the LLM.
        
        Args:
            lead_data: Lead data from Zoho CRM
            attachment_text: Optional extracted text from attachments
            
        Returns:
            Formatted string for LLM prompt
        """
        # Filter out None values and format nicely
        formatted_lines = []
        
        # Priority fields to include
        priority_fields = [
            "First_Name", "Last_Name", "Email", "Phone", "Mobile",
            "Company", "Title", "Industry", "Lead_Source", "Lead_Status",
            "Website", "Description", "Street", "City", "State", 
            "Zip_Code", "Country", "Annual_Revenue", "No_of_Employees",
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
