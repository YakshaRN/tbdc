# TBDC Platform - Architecture Document

## Overview

TBDC (Toronto Business Development Centre) is a CRM-integrated AI platform that evaluates global startups for Canada/North America market fit. It has two primary modules -- **Lead Module** (Pivot program) and **Application Module** (Deal/Application program) -- both powered by AI analysis via AWS Bedrock (Claude), with Zoho CRM as the source of truth.

**Tech Stack:**
- **Backend:** Python / FastAPI
- **Frontend:** Next.js 16 / React 19 / TypeScript / Tailwind CSS
- **LLM:** AWS Bedrock (Claude 3 Sonnet + Titan Embeddings)
- **Database/Cache:** AWS DynamoDB
- **CRM:** Zoho CRM API v7
- **Meeting Transcripts:** Fireflies.ai GraphQL API
- **Vector Search:** FAISS (in-memory + persisted to disk)

---

## 1. Background Processes

These processes run automatically and are not triggered by user actions on leads or deals.

### 1.1 Zoho OAuth Authentication & Token Refresh

**Files:** `services/zoho/token_manager.py`, `middleware/zoho_token.py`, `api/v1/endpoints/auth.py`

#### Initial OAuth Flow (one-time manual setup)
1. Admin visits `GET /api/v1/auth/zoho/authorize`
2. Backend redirects to Zoho's OAuth consent page at `{ZOHO_ACCOUNTS_URL}/oauth/v2/auth` with scopes: `ZohoCRM.modules.ALL`, `ZohoCRM.settings.ALL`, `ZohoCRM.users.ALL`
3. User authorizes and Zoho redirects back to `GET /api/v1/auth/zoho/callback` with an authorization code
4. Backend exchanges the code for tokens via `POST {ZOHO_ACCOUNTS_URL}/oauth/v2/token` with `grant_type=authorization_code`
5. The `refresh_token` is saved to the `.env` file (it does not expire)

**External Communication:** HTTPS POST to `https://accounts.zoho.com/oauth/v2/token`

#### Background Token Refresh (runs continuously)
1. On application startup (`main.py` lifespan), `zoho_token_manager.initialize()` is called
2. It makes an initial token refresh via `POST {ZOHO_ACCOUNTS_URL}/oauth/v2/token` with `grant_type=refresh_token`
3. It starts an **asyncio background task** (`_start_background_refresh()`) that runs in a perpetual loop
4. The task sleeps until `token_expiry - ZOHO_TOKEN_REFRESH_BUFFER` (default: 5 minutes before the 1-hour expiry)
5. It then refreshes the access token via the same `POST` endpoint
6. On failure, it retries after 60 seconds
7. Uses an `asyncio.Lock` to prevent race conditions during concurrent refresh attempts
8. On application shutdown, the background task is cancelled and the HTTP client is closed

**External Communication:** HTTPS POST to `https://accounts.zoho.com/oauth/v2/token` (every ~55 minutes)

#### Zoho Token Middleware (per-request)
1. Intercepts all requests to `/api/v1/zoho/`, `/api/v1/leads/`, `/api/v1/contacts/`, `/api/v1/deals/`
2. Calls `zoho_token_manager.get_access_token()` to get the current valid token
3. Attaches the token to `request.state.zoho_token` for downstream use
4. Skips `/health`, `/docs`, `/redoc`, and `/api/v1/auth/zoho/` routes

---

### 1.2 DynamoDB Table Initialization

**Files:** `services/dynamodb/lead_cache.py`, `services/dynamodb/deal_cache.py`, `services/dynamodb/prompt_store.py`

On application startup (`main.py` lifespan):
1. Checks if DynamoDB is enabled (`DYNAMODB_ENABLED=true`)
2. Creates the **leads** table (configurable name via `DYNAMODB_TABLE_NAME`, default `leads`) if it doesn't exist -- primary key: `lead_id`
3. Creates the **deals** table (configurable name via `DYNAMODB_DEAL_TABLE_NAME`, default `tbdc_deal_analysis`) if it doesn't exist -- primary key: `deal_id`
4. Creates the **prompts** table (configurable name via `DYNAMODB_PROMPTS_TABLE_NAME`, default `prompts`) if it doesn't exist -- primary key: `prompt_key`

**External Communication:** AWS DynamoDB API via boto3 SDK

---

### 1.3 Prompt Seeding

**Files:** `services/dynamodb/prompt_seed.py`, `services/dynamodb/prompt_store.py`

1. On first read of prompts, if the DynamoDB prompts table is empty, seed prompts are written from `prompt_seed.py`
2. There are **6 prompt keys** stored:
   - `system_prompt` -- Lead analysis system prompt
   - `analysis_prompt` -- Lead analysis user prompt template (placeholder: `{lead_data}`)
   - `deal_system_prompt` -- Deal analysis system prompt (includes TBDC pricing catalog)
   - `deal_analysis_prompt` -- Deal analysis user prompt template (placeholder: `{deal_data}`)
   - `deal_scoring_system_prompt` -- Deal scoring system prompt (9-category weighted rubric)
   - `deal_scoring_prompt` -- Deal scoring user prompt template (placeholders: `{deal_data}`, `{analysis_summary}`)
3. After initial seeding, all prompt reads/writes go through DynamoDB with **no in-memory cache** (always fresh from DB)

**External Communication:** AWS DynamoDB API via boto3 SDK

---

### 1.4 Marketing Materials Embedding & Indexing

**Files:** `services/vector/embedding_service.py`, `services/vector/marketing_vector_store.py`

This is triggered via the `POST /api/v1/marketing/index` endpoint (admin uploads an Excel file):

1. Admin uploads an Excel file with columns: `Collateral Title`, `LINK`, `Industry`, `Business Topics`, `Other Notes`
2. For each row, a combined text representation is built from all columns
3. Each text is sent to **AWS Bedrock Titan Embeddings** (`amazon.titan-embed-text-v1`) to generate a **1536-dimensional** vector
4. Vectors are L2-normalized and indexed into a **FAISS** `IndexFlatIP` (Inner Product) index for cosine similarity search
5. The index is persisted to disk at `data/vector_store/marketing_index.faiss` and metadata at `data/vector_store/marketing_metadata.pkl`
6. Subsequent searches use the persisted index (loaded on first access)

**External Communication:** AWS Bedrock Runtime API -- `invoke_model` with model `amazon.titan-embed-text-v1`

---

### 1.5 User Authentication (JWT)

**Files:** `services/dynamodb/user_service.py`, `core/security.py`, `api/v1/endpoints/users.py`

1. User signs up via `POST /api/v1/users/signup` -- password is hashed with SHA-256 + random salt, stored in DynamoDB `tbdc_users` table
2. User logs in via `POST /api/v1/users/login` -- returns a JWT token (HS256, 24-hour expiry)
3. Protected endpoints verify the JWT via `Authorization: Bearer <token>` header

**External Communication:** AWS DynamoDB API for user storage

---

## 2. Lead Module (Pivot Program)

**Files:** `api/v1/endpoints/leads.py`, `services/llm/bedrock_service.py`, `services/llm/similar_customers_service.py`, `services/vector/marketing_vector_store.py`, `services/web/scraper.py`, `services/document/extractor.py`, `services/dynamodb/lead_cache.py`

### 2.1 List Leads -- `GET /api/v1/leads/`

**Steps:**
1. Parse optional query parameters: `page`, `per_page`, `sort_by`, `sort_order`, `fields`, `lead_source`, `fetch_all`
2. If `lead_source` filter is provided, build Zoho search criteria: `(Lead_Source:equals:{lead_source})`
3. If `fetch_all=true`, call `zoho_crm_service.search_all_leads()` which paginates through all pages (up to 2000 records)
4. Otherwise call `zoho_crm_service.get_leads()` with pagination parameters
5. Return `LeadListResponse` with data, page, per_page, total_count, more_records

**External Communication:**
- Zoho CRM API: `GET https://www.zohoapis.com/crm/v7/Leads` (with `Authorization: Zoho-oauthtoken {token}`)

---

### 2.2 Get Lead with AI Analysis -- `GET /api/v1/leads/{lead_id}`

This is the core enrichment endpoint. **Steps:**

#### Step 1: Fetch Lead from Zoho
- Call `zoho_crm_service.get_lead_by_id(lead_id)`
- **External Communication:** `GET https://www.zohoapis.com/crm/v7/Leads/{lead_id}`

#### Step 2: Check DynamoDB Cache
- Call `lead_analysis_cache.get_cached_data(lead_id)` (skipped if `refresh_analysis=true`)
- If cache hit, return cached analysis + marketing materials + similar customers immediately
- **External Communication:** AWS DynamoDB `get_item` on `leads` table

#### Step 3: Fetch & Extract Attachments (on cache miss)
- Call `zoho_crm_service.get_lead_attachments_with_content(lead_id)`
  - First fetches attachment list: `GET https://www.zohoapis.com/crm/v7/Leads/{lead_id}/Attachments`
  - Then downloads each attachment: `GET https://www.zohoapis.com/crm/v7/Leads/{lead_id}/Attachments/{attachment_id}`
- Extract text from downloaded files using `document_extractor`:
  - PDF: via `pypdf`
  - DOCX: via `python-docx`
  - PPTX: via `python-pptx`
  - XLSX: via `openpyxl`
  - TXT/CSV: direct read
- **External Communication:** Zoho CRM API (attachment list + download)

#### Step 4: Scrape Website & LinkedIn (parallel, on cache miss)
- Extract `Website` URL and `LinkedIn_Profile` URL from lead data
- Run both scrapes in parallel via `asyncio.gather`:
  - `website_scraper.fetch_page_text(website_url)` -- HTTP GET to the company website, parse with BeautifulSoup, extract visible text (max 5000 chars)
  - `website_scraper.fetch_page_text(linkedin_url)` -- HTTP GET to the LinkedIn profile URL, extract visible text
- Both are best-effort; failures return `None` and the flow continues
- **External Communication:** HTTP GET to the lead's company website and LinkedIn URL

#### Step 5: LLM Call #1 -- Lead Analysis
- Build prompt by combining: lead CRM fields + attachment text + website text + LinkedIn text
- Load system prompt and analysis prompt template from DynamoDB via `prompt_manager`
- Call `bedrock_service.invoke_claude()` with:
  - **Model:** `anthropic.claude-3-sonnet-20240229-v1:0` (configurable via `BEDROCK_MODEL_ID`)
  - **Max Tokens:** 4096 (default)
  - **Temperature:** 0.3
  - **Anthropic Version:** `bedrock-2023-05-31`
- LLM returns structured JSON with: company_name, country, region, summary, product_description, vertical, business_model, motion, raise_stage, company_size, likely_icp_canada, fit_score (1-10), fit_assessment, key_insights, questions_to_ask, confidence_level, notes
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model`
- **Note on "web searches" in prompt:** The system prompt instructs the LLM to "review the company's official website" and "use 2-3 max third-party sources." However, the LLM does **NOT** have internet access or tool-use capabilities. It relies on (a) the scraped website/LinkedIn text provided in the prompt context, and (b) its training data knowledge. There is no actual web search API call.

#### Step 6: Search Marketing Materials
- Call `marketing_vector_store.search_for_lead(lead_data)` which:
  - Builds a text representation from lead fields (Company, Industry, Description, Title, etc.)
  - Generates an embedding via `amazon.titan-embed-text-v1`
  - Searches the FAISS index for top-k similar marketing materials
- Returns matched materials with title, link, industry, business_topics, similarity_score
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model` (Titan Embeddings)

#### Step 7: LLM Call #2 -- Similar Customers
- Call `similar_customers_service.find_similar_customers(lead_data, analysis_data)`
- Builds a prompt with lead info + analysis context, asking the LLM to suggest 3 real Canadian/NA companies
- Call `bedrock_service.invoke_claude()` with:
  - **Temperature:** 0.5 (slightly higher for diversity)
  - Same model as above
- LLM returns JSON with: typical_customer_profile, target_industries, target_company_size, and 3 similar_customers (name, description, industry, website, why_similar)
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model`
- **Note on "web search":** Despite the module docstring mentioning "web search to find real companies," this service does **NOT** perform any web searches. It relies entirely on the LLM's training knowledge to suggest real companies.

#### Step 8: Cache Results
- Save analysis + marketing materials + similar customers to DynamoDB
- **External Communication:** AWS DynamoDB `put_item` on `leads` table

#### Step 9: Return Response
- Return `EnrichedLeadResponse` with: data, analysis, analysis_available, from_cache, marketing_materials, similar_customers

---

### 2.3 Create Lead -- `POST /api/v1/leads/`
1. Validate request body against `LeadCreate` schema
2. Call `zoho_crm_service.create_lead(data)`
3. **External Communication:** `POST https://www.zohoapis.com/crm/v7/Leads`

### 2.4 Update Lead -- `PUT /api/v1/leads/{lead_id}`
1. Validate request body against `LeadUpdate` schema
2. Call `zoho_crm_service.update_lead(lead_id, data)`
3. **External Communication:** `PUT https://www.zohoapis.com/crm/v7/Leads`

### 2.5 Delete Lead -- `DELETE /api/v1/leads/{lead_id}`
1. Call `zoho_crm_service.delete_lead(lead_id)`
2. **External Communication:** `DELETE https://www.zohoapis.com/crm/v7/Leads?ids={lead_id}`

### 2.6 Search Leads -- `GET /api/v1/leads/search/`
1. Build Zoho search criteria from: `criteria` (raw), `search_query` (OR across First_Name, Last_Name, Email, Company, Owner.name using `starts_with`), or individual field filters (AND conditions)
2. Call `zoho_crm_service.search_leads(criteria)`
3. **External Communication:** `GET https://www.zohoapis.com/crm/v7/Leads/search?criteria=...`

---

## 3. Application Module (Deal/Application Program)

**Files:** `api/v1/endpoints/deals.py`, `services/llm/deal_analysis_service.py`, `services/llm/similar_customers_service.py`, `services/fireflies/fireflies_service.py`, `services/vector/marketing_vector_store.py`, `services/document/extractor.py`, `services/dynamodb/deal_cache.py`

### 3.1 List Deals -- `GET /api/v1/deals/`

**Steps:**
1. Parse optional query parameters: `page`, `per_page`, `sort_by`, `sort_order`, `fields`, `stage`, `fetch_all`
2. If `stage` filter provided, build criteria: `(Stage:equals:{stage})`
3. If `fetch_all=true`, call `zoho_crm_service.search_all_deals()` (paginates through all pages, up to 2000 records)
4. Otherwise call `zoho_crm_service.get_deals()` with pagination
5. Return `DealListResponse`

**External Communication:**
- Zoho CRM API: `GET https://www.zohoapis.com/crm/v7/Deals`

---

### 3.2 Get Deal with AI Analysis -- `GET /api/v1/deals/{deal_id}`

This is the core enrichment endpoint for deals. It makes **3 LLM calls** (vs. 2 for leads) and adds Fireflies meeting notes.

#### Step 1: Fetch Deal from Zoho
- Call `zoho_crm_service.get_deal_by_id(deal_id)`
- **External Communication:** `GET https://www.zohoapis.com/crm/v7/Deals/{deal_id}`

#### Step 2: Check DynamoDB Cache
- Call `deal_analysis_cache.get_cached_data(deal_id)` (skipped if `refresh_analysis=true`)
- If cache hit, return cached analysis + marketing materials + similar customers immediately
- **External Communication:** AWS DynamoDB `get_item` on `tbdc_deal_analysis` table

#### Step 3: Fetch & Extract Attachments (on cache miss)
- Call `zoho_crm_service.get_deal_attachments_with_content(deal_id)`
  - Fetches attachment list: `GET https://www.zohoapis.com/crm/v7/Deals/{deal_id}/Attachments`
  - Downloads each attachment: `GET https://www.zohoapis.com/crm/v7/Deals/{deal_id}/Attachments/{attachment_id}`
- Extract text from files using `document_extractor` (same as leads)
- **External Communication:** Zoho CRM API (attachment list + download)

#### Step 4: Fetch Fireflies Meeting Notes (on cache miss)
- Resolve contact email: extract `Contact_Name` from deal data (may be `{id, name}` object), then fetch the contact from Zoho to get their email
  - **External Communication:** `GET https://www.zohoapis.com/crm/v7/Contacts/{contact_id}` (if Contact_Name is an ID reference)
- Call `fireflies_service.get_meeting_notes_for_email(contact_email)`:
  - **GraphQL Query 1:** `{ transcripts { id participants } }` -- fetches ALL transcripts, filters client-side by matching participant email
    - **External Communication:** `POST https://api.fireflies.ai/graphql` with Bearer token
  - **GraphQL Query 2 (per matched transcript):** `{ transcript(id: "...") { id title summary { notes action_items } } }` -- fetches the summary for each matched transcript
    - **External Communication:** `POST https://api.fireflies.ai/graphql` (one call per matched transcript)
  - Combines all matched meeting notes into a single formatted text block with title, notes, and action items

#### Step 5: LLM Call #1 -- Main Deal Analysis
- Build prompt by combining: deal CRM fields + attachment text + meeting notes text
- Special deal fields included for LLM reformatting:
  - **Revenue fields:** Projected_company_revenue_in_current_fisca, Sales_revenue_since_being_incorporated, Company_revenue_in_current_fiscal_year_CAD, Company_Monthly_Revenue, Revenue_Range, Company_revenue_in_last_fiscal_year_CAD
  - **Customer fields:** Top_5_Customers, Target_Markets_or_Customer_Segments, Target_Customer_Type, Customer_Example
  - **Support fields:** Specific_Area_of_Support_Required
- Load deal system prompt and analysis prompt template from DynamoDB via `prompt_manager`
- The system prompt includes the **TBDC Service Pricing Catalog** (see section 5 below)
- Call `bedrock_service.invoke_claude()` with:
  - **Model:** `anthropic.claude-3-sonnet-20240229-v1:0` (configurable)
  - **Max Tokens:** 8192 (higher than lead analysis due to richer output)
  - **Temperature:** 0.3
- LLM returns JSON with: company_name, country, region, summary, product_description, vertical, business_model, motion, raise_stage, company_size, **revenue_summary**, **top_5_customers_summary**, **icp_mapping**, **support_required**, **pricing_summary** (with recommended_services, total_cost_eur, pricing_notes), key_insights, questions_to_ask, confidence_level, notes
- Has truncated JSON repair logic to handle cases where the response exceeds max_tokens
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model`

#### Step 6: LLM Call #2 -- Scoring Rubric
- Build a concise analysis summary from Step 5 results (company, product, vertical, ICP, support, key insights, top customers)
- Load scoring system prompt and scoring prompt template from DynamoDB
- The scoring system prompt defines a **9-category weighted rubric:**
  1. Product Maturity / Technology Readiness (15%)
  2. Founder Readiness + Team Capability (15%)
  3. Revenue / Product Validation (15%)
  4. Market Readiness (10%)
  5. Competitive Landscape (10%)
  6. Funding Position (10%)
  7. Regulatory Awareness (10%)
  8. Strategic Fit (10%)
  9. Materials Preparedness (5%)
- Special scoring rules: B2C companies always get Strategic Fit = 1; MVP-stage companies capped at 2/5 for Product Maturity
- Call `bedrock_service.invoke_claude()` with:
  - **Max Tokens:** 1024 (smaller, focused response)
  - **Temperature:** 0.2 (lower for consistent scoring)
- LLM returns JSON with: scoring_rubric (product_market_fit, canada_market_readiness, gtm_clarity, team_capability, revenue_potential), fit_score (1-10), fit_assessment
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model`

#### Step 7: Search Marketing Materials
- Same flow as Lead Module Step 6 (FAISS vector search with Titan embeddings)
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model` (Titan Embeddings)

#### Step 8: LLM Call #3 -- Similar Customers
- Same flow as Lead Module Step 7
- **External Communication:** AWS Bedrock Runtime API -- `invoke_model`

#### Step 9: Cache Results
- Save analysis + marketing materials + similar customers to DynamoDB
- **External Communication:** AWS DynamoDB `put_item` on `tbdc_deal_analysis` table

#### Step 10: Return Response
- Return `EnrichedDealResponse` with: data, analysis, analysis_available, from_cache, marketing_materials, similar_customers

---

### 3.3 Create Deal -- `POST /api/v1/deals/`
1. Validate request body against `DealCreate` schema
2. Call `zoho_crm_service.create_deal(data)`
3. **External Communication:** `POST https://www.zohoapis.com/crm/v7/Deals`

### 3.4 Update Deal -- `PUT /api/v1/deals/{deal_id}`
1. Validate request body against `DealUpdate` schema
2. Call `zoho_crm_service.update_deal(deal_id, data)`
3. **External Communication:** `PUT https://www.zohoapis.com/crm/v7/Deals`

### 3.5 Delete Deal -- `DELETE /api/v1/deals/{deal_id}`
1. Call `zoho_crm_service.delete_deal(deal_id)`
2. **External Communication:** `DELETE https://www.zohoapis.com/crm/v7/Deals?ids={deal_id}`

### 3.6 Search Deals -- `GET /api/v1/deals/search/`
1. Build Zoho search criteria from: `criteria` (raw), `search_query` (OR across Deal_Name, Account_Name, Contact_Name, Owner.name), or individual field filters
2. Call `zoho_crm_service.search_deals(criteria)`
3. **External Communication:** `GET https://www.zohoapis.com/crm/v7/Deals/search?criteria=...`

---

## 4. Other Modules

### 4.1 Web Evaluation Module -- `GET /api/v1/web/evaluate`

Provides a standalone website evaluation pipeline (not tied to a Zoho lead):

1. Normalize domain from URL to create cache key `web_{domain}`
2. Check DynamoDB cache (`leads` table)
3. If cache miss: scrape website metadata + page text via `httpx` + `BeautifulSoup`
4. Build a lead-like data structure from scraped info (company_name, description, industry hints, etc.)
5. Run LLM analysis (same as Lead Module Step 5)
6. Find similar customers (same as Lead Module Step 7)
7. Find marketing materials (same as Lead Module Step 6)
8. Cache in DynamoDB under `web_{domain}`
9. Return `EnrichedLeadResponse`

**External Communication:** HTTP GET (target website), AWS Bedrock (Claude + Titan), AWS DynamoDB

### 4.2 Marketing Module -- `POST /api/v1/marketing/index`

See section 1.4 above. Additional endpoints:
- `GET /marketing/search` -- semantic similarity search (query text -> Titan embedding -> FAISS search)
- `GET /marketing/status` -- returns index stats (total materials, embedding dimension, etc.)
- `DELETE /marketing/clear` -- removes the FAISS index and metadata files from disk
- `GET /marketing/materials` -- lists all indexed materials with pagination

### 4.3 Settings Module -- `/api/v1/settings/prompts`

- `GET /settings/prompts` -- returns all 6 LLM prompts from DynamoDB
- `PUT /settings/prompts` -- updates prompts (validates that required placeholders like `{lead_data}` and `{deal_data}` are present)

---

## 5. AWS Bedrock Models Used

| Model | Model ID | Purpose | Parameters |
|-------|----------|---------|------------|
| **Claude 3 Sonnet** | `anthropic.claude-3-sonnet-20240229-v1:0` (default, configurable via `BEDROCK_MODEL_ID` env var) | All LLM text generation (lead analysis, deal analysis, scoring rubric, similar customers) | `anthropic_version: bedrock-2023-05-31` |
| **Titan Embed Text v1** | `amazon.titan-embed-text-v1` (hardcoded) | Text embeddings for marketing material vector search | 1536 dimensions, 8000 char input limit |

### LLM Call Parameters by Use Case

| Use Case | Max Tokens | Temperature | File |
|----------|-----------|-------------|------|
| Lead Analysis | 4096 | 0.3 | `bedrock_service.py` |
| Deal Main Analysis | 8192 | 0.3 | `deal_analysis_service.py` |
| Deal Scoring Rubric | 1024 | 0.2 | `deal_analysis_service.py` |
| Similar Customers | 4096 | 0.5 | `similar_customers_service.py` |

---

## 6. All External Communications Summary

| # | Service | Protocol | URL / Endpoint | Auth Method | Purpose |
|---|---------|----------|---------------|-------------|---------|
| 1 | **Zoho CRM API v7** | REST/HTTPS | `https://www.zohoapis.com/crm/v7/{module}` | `Zoho-oauthtoken {access_token}` | CRUD for Leads, Deals, Contacts; attachment downloads; search |
| 2 | **Zoho OAuth** | HTTPS POST | `https://accounts.zoho.com/oauth/v2/token` | `client_id` + `client_secret` + `refresh_token` | Access token refresh (every ~55 min) |
| 3 | **AWS Bedrock Runtime (Claude)** | AWS SDK (boto3) | Regional (`us-east-1` default) | AWS IAM / explicit keys | LLM text generation (analysis, scoring, similar customers) |
| 4 | **AWS Bedrock Runtime (Titan)** | AWS SDK (boto3) | Regional (`us-east-1` default) | AWS IAM / explicit keys | Text embedding generation for vector search |
| 5 | **AWS DynamoDB** | AWS SDK (boto3) | Regional | AWS IAM / explicit keys | Caching (lead analysis, deal analysis), prompt storage, user management |
| 6 | **Fireflies.ai** | GraphQL/HTTPS | `https://api.fireflies.ai/graphql` | `Bearer {FIREFLIES_API_KEY}` | Meeting transcript summaries (used in deal analysis only) |
| 7 | **Company Websites** | HTTP/HTTPS GET | Any URL from lead/deal data | None (User-Agent spoofing) | Scraping company website text for LLM context |
| 8 | **LinkedIn Profiles** | HTTP/HTTPS GET | LinkedIn URLs from lead data | None (User-Agent spoofing) | Scraping LinkedIn profile text for LLM context (lead module only) |

---

## 7. Web Searches & Internet Access -- Explicit Clarification

### What the LLM prompts say vs. what actually happens

The **lead analysis system prompt** instructs the LLM:
> "Always review the company's official website first (homepage, product, solutions, or industries pages)."
> "Use 2-3 max third-party sources to cross-check information/reviews about the company."

The **deal analysis system prompt** has similar instructions.

**However, the LLM does NOT have internet access or tool-use capabilities.** All LLM calls are simple prompt-in/text-out invocations via `invoke_model`. There are:
- **No web search APIs** (no Tavily, no Google Search, no Bing API)
- **No LLM tool use / function calling** (no `tools` blocks in the Bedrock request payload)
- **No browsing capabilities** for the LLM

Instead, the system provides context to the LLM by:
1. **Pre-scraping the company website** using `WebScraperService` (`httpx` + `BeautifulSoup`) and injecting the text into the prompt as `=== SCRAPED WEBSITE CONTENT ===`
2. **Pre-scraping the LinkedIn profile** (lead module only) and injecting it as `=== SCRAPED LINKEDIN PROFILE ===`
3. **Extracting attachment text** (PDFs, DOCX, PPTX) and injecting it as `=== ATTACHED DOCUMENTS ===`
4. **Fetching meeting notes** from Fireflies.ai (deal module only) and injecting them as `=== MEETING NOTES (Fireflies.ai) ===`

The LLM then uses this pre-fetched context along with its **training data knowledge** to generate the analysis. When the prompt says "use third-party sources," the LLM draws from its training knowledge -- it cannot make real-time web requests.

Similarly, the **Similar Customers Service** docstring mentions "web search to find real companies," but the implementation only uses an LLM call. The LLM suggests real companies based on its training data, not live search results.

---

## 8. LLM Calls Per Request Summary

| Endpoint | LLM Calls | Embedding Calls | Total Bedrock Calls |
|----------|-----------|-----------------|---------------------|
| `GET /leads/{id}` (cache miss) | 2 (analysis + similar customers) | 1 (marketing search) | 3 |
| `GET /deals/{id}` (cache miss) | 3 (analysis + scoring + similar customers) | 1 (marketing search) | 4 |
| `GET /web/evaluate` (cache miss) | 2 (analysis + similar customers) | 1 (marketing search) | 3 |
| `POST /marketing/index` | 0 | N (one per material row) | N |
| `GET /marketing/search` | 0 | 1 (query embedding) | 1 |
| Any cached request | 0 | 0 | 0 |

---

## 9. TBDC Service Pricing Catalog (embedded in deal analysis prompt)

The deal analysis LLM is given this pricing catalog to recommend services:

| Category | Service | Price (EUR) |
|----------|---------|-------------|
| Core | Scout Report | 4,000 |
| Core | Mentor Hours (x4 hours) | 2,000 |
| Core | Startup Ecosystem Events | 0 (included) |
| Core | Investor & Regulatory Sessions | 0 (included) |
| Core | Office Access & Meeting Rooms | 0 (included) |
| Core | $500k Tech Credits | 0 (included) |
| Customer Meetings | Enterprise Meetings | 2,000 each |
| Customer Meetings | SMB Meetings | 1,500 each |
| Investor Meetings | Category A | 2,500 each |
| Investor Meetings | Category B | 1,500 each |
| Additional | Deal Memo | 2,000 |

The LLM selects appropriate services based on company profile and calculates total cost.

---

## 10. Data Flow Diagrams

### Lead Enrichment Flow (cache miss)
```
User Request
    |
    v
[GET /leads/{id}]
    |
    +---> [Zoho CRM] Fetch lead data
    |
    +---> [DynamoDB] Check cache --> (cache hit? return early)
    |
    +---> [Zoho CRM] Fetch attachments --> [Document Extractor] Extract text
    |
    +---> [Company Website] Scrape text --|
    +---> [LinkedIn Profile] Scrape text --|--> (parallel)
    |
    +---> [AWS Bedrock / Claude] LLM Call #1: Lead Analysis
    |
    +---> [AWS Bedrock / Titan] Generate embedding --> [FAISS] Search marketing materials
    |
    +---> [AWS Bedrock / Claude] LLM Call #2: Similar Customers
    |
    +---> [DynamoDB] Cache results
    |
    v
EnrichedLeadResponse
```

### Deal Enrichment Flow (cache miss)
```
User Request
    |
    v
[GET /deals/{id}]
    |
    +---> [Zoho CRM] Fetch deal data
    |
    +---> [DynamoDB] Check cache --> (cache hit? return early)
    |
    +---> [Zoho CRM] Fetch attachments --> [Document Extractor] Extract text
    |
    +---> [Zoho CRM] Fetch contact --> [Fireflies.ai] Fetch meeting notes (GraphQL)
    |
    +---> [AWS Bedrock / Claude] LLM Call #1: Main Deal Analysis (8192 tokens)
    |
    +---> [AWS Bedrock / Claude] LLM Call #2: Scoring Rubric (1024 tokens)
    |
    +---> [AWS Bedrock / Titan] Generate embedding --> [FAISS] Search marketing materials
    |
    +---> [AWS Bedrock / Claude] LLM Call #3: Similar Customers
    |
    +---> [DynamoDB] Cache results
    |
    v
EnrichedDealResponse
```
