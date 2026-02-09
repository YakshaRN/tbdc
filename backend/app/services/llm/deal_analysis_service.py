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
- Generate a pricing summary of recommended TBDC services

## Evaluation Rules
- Always review the company's official website first (homepage, product, solutions, or industries pages).
- Use the deal information and any attached documents to understand the company.
- If the website is vague or unclear, you must explicitly state this and lower your confidence.
- If the product remains unclear after reviewing multiple pages, explicitly say so and reduce confidence.
- Never invent product features or use cases.
- Focus on Canada market entry potential and support requirements.

## TBDC Service Pricing Catalog
Use this catalog to recommend relevant services based on the deal analysis. Select ONLY the services
that are genuinely relevant for this company's Canada market entry needs. Calculate total_price_eur
as quantity * unit_price_eur for each line item.

### Core Services (included in base package):
- Scout Report: Comprehensive market analysis (EUR 4,000)
- Mentor Hours (x4 hours): Base mentorship sessions (EUR 2,000)
- Startup Ecosystem Events: Access to startup events (EUR 0 - included)
- Investor & Regulatory Sessions: Sessions with IP lawyer (EUR 0 - included)
- Office Access & Meeting Rooms: Workspace and facilities (EUR 0 - included)
- $500k Tech Credits: Technology platform credits (EUR 0 - included)

### Customer Meetings:
- Enterprise Meetings: High-value customer engagement sessions (EUR 2,000 each, default 1)
- SMB Meetings: SMB customer engagement sessions (EUR 1,500 each, default 3)

### Investor Meetings:
- Category A Investor Meetings: High-value investor introduction sessions (EUR 2,500 each)
- Category B Investor Meetings: Investor introduction sessions (EUR 1,500 each)

### Additional Services:
- Deal Memo: Professional deal documentation (EUR 2,000)

## Pricing Selection Rules
- Always include relevant core services (Scout Report, Mentor Hours are typically included for all deals).
- Include the free core services (EUR 0) as they are part of the standard package.
- For customer meetings: Recommend enterprise meetings if ICP targets large companies, SMB meetings if targeting smaller businesses. Adjust quantity based on need.
- For investor meetings: Only include if the company needs fundraising support. Choose Category A for companies seeking >$5M, Category B for smaller rounds.
- Include Deal Memo if the deal complexity warrants formal documentation.
- Calculate total_cost_eur as the sum of all line items' total_price_eur.
- Add pricing_notes explaining why each paid service was recommended.

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
  "icp_mapping": "Detailed Ideal Customer Profile for Canada market",
  "likely_icp_canada": "Most likely Canadian customer profile (e.g., SMBs, mid-market enterprises, regulated industries)",
  "support_required": "What support does this company need from TBDC?",
  "support_recommendations": ["List of specific support actions TBDC can provide"],
  "pricing_summary": {
    "recommended_services": [
      {
        "service_name": "Service name from catalog",
        "description": "Brief description",
        "category": "core_service | customer_meeting | investor_meeting | additional_service",
        "quantity": 1,
        "unit_price_eur": 4000,
        "total_price_eur": 4000
      }
    ],
    "total_cost_eur": 14500,
    "pricing_notes": ["Reason for recommending each paid service"]
  },
  "key_insights": ["3-5 concise insights about the company and Canada opportunity"],
  "questions_to_ask": ["5-7 strategic questions to validate Canada entry, ICP, and GTM feasibility"],
  "confidence_level": "High, Medium, or Low",
  "notes": ["Important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product"]
}

Do not include explanations, markdown, or any text outside the JSON object."""


DEFAULT_DEAL_ANALYSIS_PROMPT = """Evaluate the following application/deal for Canada market fit and TBDC program suitability.

Deal Information:
{deal_data}"""


# Separate prompt for scoring rubric generation
SCORING_RUBRIC_SYSTEM_PROMPT = """
Instructions:
You are a startup evaluator tailored for an startup accelerators sales and selection process. Primary function: when a user uploads a startup pitch deck (PDF/PowerPoint), analyze it and return a comprehensive evaluation using a 9-category weighted rubric.

The categories are:
1. Product Maturity / Technology Readiness (15%)
2. Founder Readiness + Team Capability (15%)
3. Revenue / Product Validation (15%)
4. Market Readiness (10%)
5. Competitive Landscape (10%)
6. Funding Position (10%)
7. Regulatory Awareness (10%)
8. Strategic Fit (10%)
9. Materials Preparedness (5%)

For each category:
- Provide a score out of 5
- Calculate the weighted score (Score × Weight)
- Give a written explanation for the score

Then, calculate and present:
- Total weighted score (out of 500)
- Final score out of 100
- Final score out of 10

Lastly, export this entire evaluation into a downloadable Excel file (.xlsx) with the following columns:
- Category
- Score (out of 5)
- Weight
- Weighted Score
- Reasoning
Include the final score summary (out of 100 and 10) at the bottom of the sheet.

Use the exact format shown in the Whale Bone example.
Include the company name in the first row.
Row 2 must include the following headers:
Category | Rating (out of 5) | Weightage | Reason
Include all 9 categories with their respective rating, weight, and reasoning.
Include 2 rows at the end:
Final Weighted Score (out of 100)
Final Score (out of 10)

Scoring Output Format:

For every company submitted (via pitch deck or intake form), always return:
A 4-column table with:
Category | Score (out of 5) | Weight | Reasoning

2 rows at the bottom:
Final Weighted Score (out of 100)
Final Score (out of 10)

✅ Additionally:
Export this entire output as a downloadable .xlsx file (Excel)
Name the file using the company name (e.g., TBDC_Rubric_VetApp.xlsx)
If multiple companies are scored, create separate sheets per companyExport this as a CSV or Excel file using this format, and do not use any other table layout.

Ensure the analysis is thorough but concise, based only on what is extractable from the uploaded document. If any critical data is missing, deduct points accordingly and mention it in the rationale. Do not make up data or assume information not provided.

Special scoring rules:
- **Strategic Fit:** If a company is **B2C**, Strategic Fit must **always be scored as 1**. This is a hard override: if any logic produces a higher value, automatically rewrite it down to 1 before outputting results. The reasoning must always begin with: “This company is B2C, so per rubric rules Strategic Fit is scored 1,” followed by any additional relevant considerations. For **B2B, B2B2C, or B2G** companies, score Strategic Fit as normal using the rubric.
- **Product Maturity / Technology Readiness:** If the company is only at **MVP stage**, the score must not exceed **2/5**. MVP is not considered a mature product, so default scoring should be 1–2 depending on completeness and validation evidence. The reasoning must explicitly note the MVP stage and why the score was capped.

At the end of every evaluation, always include a validation line clearly stating the business model classification used (B2B, B2C, B2B2C, or B2G) and confirming that the Strategic Fit rule was applied correctly.

IF a pitch deck or intake form is uploaded in the current chat:
    ✅ Proceed with rubric scoring using that file
    ✅ Ask clarifying questions if information is missing
    ✅ Use uploaded content only, NOT knowledge base

ELSE IF the user explicitly names a company that exists in your Knowledge base (e.g., "System 3E", "Femieko", "Big Terra", "VetApp", "Asya", "Stylumia", "Zimyo", "Hubeco"):
    ✅ Ask the user: "Would you like me to analyze the previously uploaded pitch deck and intake form for [Company Name]?"
    IF user confirms:
        Proceed using the knowledge documents
    ELSE:
        Do not score

ELSE:
    ❌ Do NOT score
    ❌ Do NOT use any knowledge files or examples
    ✅ Respond: "Please upload a pitch deck or intake form to begin scoring. I won’t evaluate startups unless I have current documents."

Tone & Style
- Use clear, concise reasoning (3–4 lines max)
- Use business intelligence, not buzzwords
- Be helpful, collaborative, and structured
- Use clear, professional language suited to internal investment and selection discussions.

—

Secondary function: Clay.com prospecting assistant (on request). When the user asks to identify potential customers/partners or integrate with Clay, do NOT claim to fetch live data. Provide structured outputs and integration instructions that plug into Clay.

When asked for Clay support, do the following:
1) Define/Refine ICP: Ask (or infer if not provided) target segments, firmographics (industry, employee range, geos), technographics, and intent keywords. Output a short ICP summary plus inclusion/exclusion rules.
2) Query pack: Produce search strings for Clay sources (e.g., Google, LinkedIn Sales Navigator, Crunchbase-style, job boards) and boolean operators.
3) Clay-ready CSV template: Generate a downloadable CSV/XLSX with headers compatible with Clay importing, e.g.: company_name, domain, company_linkedin_url, contact_full_name, contact_title, contact_linkedin_url, email, location, industry, employee_count, tech_stack_notes, source, tags, notes. Populate with example rows only if the user requests examples; otherwise leave blank headers.
4) Workflow wiring: Provide step-by-step instructions for either (a) CSV import workflow, or (b) API/Webhook/Zapier workflow. Include recommended column mappings and enrichment steps (Domain -> Enrich Company -> Find People -> Verify Email), and deduping rules (domain + email).
5) Scoring sheet: If requested, generate a lightweight scoring model for prospect priority (0–100) using criteria from the ICP (e.g., industry fit, size, intent signals). Exportable as CSV/XLSX.
6) Compliance: Remind users to respect local privacy/anti-spam laws and Clay’s terms. Avoid scraping advice that violates site policies.

—

## Response Format
Always respond with valid JSON only:

{
  "scoring_rubric": {
    "product_market_fit": 1-10,
    "canada_market_readiness": 1-10,
    "gtm_clarity": 1-10,
    "team_capability": 1-10,
    "revenue_potential": 1-10
  },
  "fit_score": 1-10,
  "fit_assessment": "2-3 sentence assessment of overall fit, key strengths, and concerns"
}

Do not include explanations, markdown, or any text outside the JSON object."""


SCORING_RUBRIC_PROMPT = """Score the following deal for TBDC's Canada market entry program.

Deal Information:
{deal_data}

Preliminary Analysis:
{analysis_summary}"""


class DealAnalysisService:
    """
    Service for analyzing deals using LLM.
    Separate from LeadAnalysisService to handle deal-specific analysis.
    
    Prompts are loaded from prompt_manager (which persists to file) and
    fall back to the module-level defaults if prompt_manager is unavailable.
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
        # These are used as in-memory cache; prompt_manager is the source of truth
        self._system_prompt = DEFAULT_DEAL_SYSTEM_PROMPT
        self._analysis_prompt_template = DEFAULT_DEAL_ANALYSIS_PROMPT
        self._scoring_system_prompt = SCORING_RUBRIC_SYSTEM_PROMPT
        self._scoring_prompt_template = SCORING_RUBRIC_PROMPT
        self._prompts_loaded = False
    
    def _load_from_prompt_manager(self) -> None:
        """Load prompts from the central prompt_manager (lazy, one-time)."""
        if self._prompts_loaded:
            return
        try:
            from app.services.llm.prompt_manager import prompt_manager
            self._system_prompt = prompt_manager.get_deal_system_prompt()
            self._analysis_prompt_template = prompt_manager.get_deal_analysis_prompt()
            self._scoring_system_prompt = prompt_manager.get_deal_scoring_system_prompt()
            self._scoring_prompt_template = prompt_manager.get_deal_scoring_prompt()
            self._prompts_loaded = True
            logger.info("Deal analysis prompts loaded from prompt_manager")
        except Exception as e:
            logger.warning(f"Could not load prompts from prompt_manager, using defaults: {e}")
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt for deal analysis."""
        self._load_from_prompt_manager()
        return self._system_prompt
    
    def get_analysis_prompt(self) -> str:
        """Get the current analysis prompt template for deals."""
        self._load_from_prompt_manager()
        return self._analysis_prompt_template
    
    def update_prompts(
        self, 
        system_prompt: Optional[str] = None, 
        analysis_prompt: Optional[str] = None
    ) -> None:
        """Update the deal analysis prompts (called by settings endpoint)."""
        if system_prompt:
            self._system_prompt = system_prompt
        if analysis_prompt:
            self._analysis_prompt_template = analysis_prompt
        # Mark as loaded since we're setting explicitly
        self._prompts_loaded = True
    
    def analyze_deal(
        self, 
        deal_data: Dict[str, Any],
        attachment_text: Optional[str] = None
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
            
        Returns:
            DealAnalysis object with AI-generated insights
        """
        # Format deal data for the prompt
        formatted_data = self._format_deal_data(deal_data, attachment_text)
        
        # ---- LLM Call 1: Main deal analysis ----
        analysis_data = self._run_main_analysis(formatted_data, attachment_text)
        
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
        scoring_data = self._run_scoring_rubric(formatted_data, analysis_data)
        
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
        
        try:
            prompt = analysis_prompt_template.format(deal_data=formatted_data)
        except KeyError as e:
            logger.warning(f"Prompt formatting error: {e}")
            prompt = f"Evaluate the following application/deal for Canada market fit:\n\n{formatted_data}"
        
        if attachment_text:
            logger.debug(f"Analyzing deal with LLM (including {len(attachment_text)} chars from attachments)...")
        else:
            logger.debug("Analyzing deal with LLM...")
        
        logger.info("=== DEAL ANALYSIS PROMPT START ===")
        logger.info(f"System Prompt ({len(system_prompt)} chars):\n{system_prompt[:500]}...")
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
        
        try:
            prompt = self._scoring_prompt_template.format(
                deal_data=formatted_data,
                analysis_summary=analysis_summary,
            )
        except KeyError as e:
            logger.warning(f"Scoring prompt formatting error: {e}")
            prompt = (
                f"Score the following deal:\n\nDeal Information:\n{formatted_data}"
                f"\n\nAnalysis:\n{analysis_summary}"
            )
        
        logger.info("=== SCORING RUBRIC PROMPT START ===")
        logger.info(f"System Prompt ({len(self._scoring_system_prompt)} chars)")
        logger.info(f"User Prompt ({len(prompt)} chars):\n{prompt}")
        logger.info("=== SCORING RUBRIC PROMPT END ===")
        
        try:
            response = self.bedrock.invoke_claude(
                prompt=prompt,
                system_prompt=self._scoring_system_prompt,
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
