
2026-02-13 20:51:21.662 | INFO     | app.services.llm.deal_analysis_service:_run_scoring_rubric:267 - === SCORING RUBRIC PROMPT START ===
2026-02-13 20:51:21.662 | INFO     | app.services.llm.deal_analysis_service:_run_scoring_rubric:268 - System Prompt (6472 chars):

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
- **Strategic Fit:** If a company is **B2C**, Strategic Fit must **always be scored as 1**. This is a hard override: if any logic produces a higher value, automatically rewrite it down to 1 before outputting results. The reasoning must always begin with: "This company is B2C, so per rubric rules Strategic Fit is scored 1," followed by any additional relevant considerations. For **B2B, B2B2C, or B2G** companies, score Strategic Fit as normal using the rubric.
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
    ✅ Respond: "Please upload a pitch deck or intake form to begin scoring. I won't evaluate startups unless I have current documents."

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
6) Compliance: Remind users to respect local privacy/anti-spam laws and Clay's terms. Avoid scraping advice that violates site policies.

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

Do not include explanations, markdown, or any text outside the JSON object.
2026-02-13 20:51:21.663 | INFO     | app.services.llm.deal_analysis_service:_run_scoring_rubric:269 - User Prompt (23129 chars):
Score the following deal for TBDC's Canada market entry program.

Deal Information:
- Deal Name: DRING
- Account Name: DRING
- Contact Name: Arda Cezzar
- Stage: Internal Review
- Probability: 35
- Type: Horizon
- Lead Source: ISB Labs
- Description: DRING builds AI-powered call centers for e-commerce, finance, and digital platforms, providing integrated and compliant agentic voice AI agents across all departments.

Signed contracts in 9 countries with a portfolio of 35 customers, DRING is a revenue-generating technology company with $425,000 in investment to date, featuring agentic AI solutions that have been active in the field since mid-2025.
- Created Time: 2026-02-10T15:03:40+05:30
- Modified Time: 2026-02-13T20:49:02+05:30
- Revenue Range: $0 - $100,000 per year
- Top 5 Customers: Easycep(refurbished electronics): B2C customer support, store hotline, survey; Figopara (supply chain financing): B2B customer reactivation; Metropolcard(employee benefit payment): B2B customer acquisition
- Target Markets or Customer Segments: We focus on the sectors where our founders and advisors have deep operational expertise. This expertise allows us to tailor our AI agents to domain-specific needs such as booking flows, marketing calls, customer acquisition or success, and post-purchase support.

Fintech Providers: As most of them operate with B2B2C business model; they require an enterprise-grade B2C customer support. They also require B2B sales/marketing outbound agents for customer acquisition. Depending on their business type, most of them serve via a platform and require an onboarding and reactivation support agent.

E-Commerce Retailers: Their service include both physical stores as well as online sales. Both sales channels require a high-level strong customer support to follow return policies, make suggestions, offer alternative product from the inventory, check for delivery status and manage support tickets in collaboration with company staff.
- Specific Area of Support Required: Global GTM Partnerships, Global References outside Turkey, Regulatory Support for Finance.
- Owner: Apply TBDC
- Received Responses: 1
- Competitive Landscapes: ORCHESTRATOR PLATFORMS: We differentiate by "direct-to-customer" approach, deep operational integrations and customer-centricity. We believe, most companies will have hard-time working on prompts, tools, integrations, tests etc. to ensure well-performing agents as part of their staff. Our participation to "outcome responsibility" is a clear edge for service.

AI AGENT ONLY COMPETITORS: We employ a human-in-the-loop system and additional virtual pbx software that enables hybrid call center working together with humans. Voice AI Agents will need to transfer some of the live calls to humans for the foreseeable future. They should also be well-placed within the IVR system of a virtual pbx. Our telco capabilities are welcomed by enterprises who prefer a smooth transition to Voice AI Agents.

VOICE AI ONLY COMPETITORS: We focus on the co-worker job role rather than solely a Voice AI on the phone. The agents we believe should also perform complementary tasks, not limiting themselves to phone calls; thus should become super-employees.
The management team of our enterprise customers are benefiting from unified intelligence and "Voice of Customer" analyses produced from interactions all across business divisions.
- LinkedIn Page URL: https://www.linkedin.com/company/dringai
- New Application Date: 2026-02-10
- Record Image: cab91424e984f1af114857784add1973eb1a5671690884b302f54f8dcc01e40e52c41645f55dae28381d83379372cefe8204e079bc1fc1b1f26528982a77c5bb1f994acfb1ec4982cf4bed5d67a8ebe2
- Country of Business Headquarters: Turkey
- Layout: Horizon
- What is Company s business model: ['B2B', 'SaaS']
- Link for BHive Mentors: https://forms.zohopublic.com/tbdc/form/MentorSurveyFormBHive/formperma/M9yp83GR-9fwODDY0JLdSgTGxuMsr9bpKGB4eJ1rbAY/?appid=5304528000096233001
- Perceived barriers of entry: ['Regulatory & Legal Compliance', 'Financial Constraints', 'Finding the right customers', 'Building a Local Network']
- Last Activity Time: 2026-02-13T20:49:02+05:30
- How much funding has been raised CAD: 425000
- Willingness to Buy Program: Medium
- In what industry does the company operate: AI
- Upload the Company Pitch Deck: [{'Created_Time__s': '2026-02-10T15:04:42+05:30', 'File_Name__s': 'DRING_Investor_Deck_December2025_final.pdf', 'Modified_Time__s': '2026-02-10T15:04:42+05:30', 'Created_By__s': {'name': 'Apply TBDC', 'id': '5304528000000367001', 'email': 'apply@tbdc.com'}, 'Size__s': 4832717, 'id': '5304528000096186020', 'Owner__s': {'name': 'Apply TBDC', 'id': '5304528000000367001', 'email': 'apply@tbdc.com'}, 'Modified_By__s': {'name': 'Apply TBDC', 'id': '5304528000000367001', 'email': 'apply@tbdc.com'}, 'File_Id__s': 'caiil9183c856979041178c30d0ed5a18c923'}]
- zohoworkdriveforcrm  Workdrive Folder ID: caiil1f52156d9db648d1a0623568a81cf21a
- Modified By: Dhruv Motwani
- Number of Active Users: 12
- Other GTM Channels: Linkedin Network
- Change Log Time  s: 2026-02-13T20:49:02+05:30
- Current Sales Channel: We already have 35+ signed enterprise deals across these verticals, proving strong early demand and demonstrating that our product solves real, high-urgency problems. We’re now expanding the product with vertical-specific capabilities, driven directly by customer needs and field data.

-The founders and initial investors are high-network individuals. A considerable portion of sales come from referrals.
-Second most effective sales method is usage of Linkedin.
-Third method would be commercial GTM partnerships.

Marketing via ads is currently not within our scope; however it would be an essential driver after we close the next investment round and automate our onboarding process.
- Go to Market Channels: ['Direct Sales', 'Partner Led Sales', 'Other']
- Created By: Apply TBDC
- Industries: ['AI']
- zohoworkdriveforcrm  Workdrive Folder URL: https://workdrive.zoho.com/folder/caiil1f52156d9db648d1a0623568a81cf21a
- How did you hear about Program: Other
- What is the current stage of the product service: Pre-Seed (<1M)
- Record Status  s: Available
- Pipeline: PivotWeek
- Company website: https://dring.ai/
- Meeting Type Preference: ['Customer Meetings', 'Partner Meetings']
- Year of Incorporation: 2024
- Link for Mentors: https://forms.zohopublic.com/tbdc/form/MentorSurveyForm/formperma/p12_dHRlETkHiowXc813p2pEw0sq1ss6GUjiPuY1QxM/?appid=5304528000096233001
- Company Incorporation status: No
- Company Name: DRING
- Share brief overview of what the Company does: DRING builds globally scalable Agentic Voice AI Agents for digital platforms, e-commerce and fintech. 

DRING's next level AI Call Center solves the problem of eliminating missed calls, increasing LTV and revenues, providing multi-lingual customer service while keeping the already existing human call center in the loop, thus providing a well-rounded service.

DRING's specialized agents act as integrated Co-Workers, who can execute "job descriptions" including handling of cold starts, reactivations, customer support and complex scheduling with human-in-the-loop design and live transfer protocols. 

DRING's agentic approach enables enterprises a complete conversational AI transformation. DRING model combines AI automation with human supervision, enabling enterprises to scale communication, increase conversion rates, and reduce operational costs without compromising quality.

DRING moves beyond point-specific solutions to provide a unified intelligence layer across all business divisions. An ecosystem of interoperable agents orchestrates the entire customer and employee lifecycle, creating a unified data loop where insights from Support instantly drive Sales and Marketing strategies.
- Current Company s Incorporated Legal Name: DRING
- Currently Fundraising: No

=== ATTACHED DOCUMENTS (Pitch Deck / PDF / Slides) ===


--- Content from: PivotWeekIntakeFormPublic.pdf ---

PivotW eek Intak e Form
Company Information


PivotW eek Intak e Form
Company Name  *
DRING
Contact Name  *
Arda
First Name Cezzar
Last Name
Contact Email  *
arda.ce zzar@dring.ai
Curr ent Role in Startup  *
CEO
What industry do you oper ate in?  *
AI
What country does your business oper ate in?
Turkey
Company Description  *
DRING builds AI-po wered call centers for e-commer ce, ﬁnance, and digital platforms, pr oviding
integr ated and compliant agentic voice AI agents acr oss all departments. 
 Signed contr acts in 9 countries with a portfolio of 35 customers, DRING is a r evenue-gener ating
technology company with $425,000 in investment to date, featuring agentic AI solutions that
have been active in the ﬁeld since mid-2025. 
 
Website  *
https://dring.ai/
Company Logo

dring_logo. png
DRING_Investor_ …pdf
Company Link edIn  *
https://www .linkedin.com/company/dringai
Founder Link edIn  *
https://www .linkedin.com/in/ar dace zzar/
Company Pitch Deck  
If no pitch deck available, please upload a document that outlines your business plan*
Year of Incorpor ation  *
2024
Are you alr eady Incorpor ated in Canada or USA?
No
What 's your business model?  *
B2B
B2C
B2B2C
B2G
C2C
SaaS
PaaS
Mark etplace
What 's your curr ent r evenue?  
Curr ent ARR*
$0 - $100,000 per year

Curr ent Stage of Company  *
Pre-Seed (<1M)
Are you curr ently fundr aising?  *
No
What ar e your Go-to-Mark et Channels?  *
Direct Sales
Partner Led Sales
Mark eting Campaigns
Other
If Other: Please specify your Go-to-Mark et Channels  *
Linkedin Network
What ar e your per ceived barriers of entry to the North American Mark et? *
Cultur al & Business Diﬀer ences
Regulatory & Legal Compliance
Financial Constr aints
Finding the right customers
Building a Local Network
Other
How did you hear about this pr ogram?
Other

PivotW eek Intak e Form
Product/Service Overvie w
Product/Service Overvie w 
Provide a detailed description of your pr oduct/service, including its k ey featur es, beneﬁts, and the speciﬁc
problems it solves for your customers.*
DRING builds globally scalable Agentic V oice AI Agents for digital platforms, e-commer ce and
ﬁntech. 
DRING' s next level AI Call Center solves the pr oblem of eliminating missed calls, incr easing L TV
and r evenues, pr oviding multi-lingual customer service while k eeping the alr eady e xisting
human call center in the loop, thus pr oviding a well-r ounded service. 
 DRING' s specialized agents act as integr ated Co-W orkers, who can e xecute "job descriptions"
including handling of cold starts, r eactivations, customer support and comple x scheduling with
human-in-the-loop design and live tr ansfer pr otocols. 
DRING' s agentic appr oach enables enterprises a complete conversational AI tr ansformation.
DRING model combines AI automation with human supervision, enabling enterprises to scale
communication, incr ease conversion r ates, and r educe oper ational costs without compr omising
quality . 
 DRING mo ves be yond point-speciﬁc solutions to pr ovide a uniﬁed intelligence layer acr oss all
business divisions. An ecosystem of inter oper able agents or chestr ates the entir e customer and
emplo yee lifecycle, cr eating a uniﬁed data loop wher e insights fr om Support instantly drive
Sales and Mark eting str ategies. 
 
Customer & Mark et Insights


PivotW eek Intak e Form
Target Mark ets or Customer Segment  
Who ar e your tar get customers and what industries/sectors do the y oper ate in?*
We focus on the sectors wher e our founders and advisors have deep oper ational e xpertise. This
expertise allo ws us to tailor our AI agents to domain-speciﬁc needs such as booking ﬂo ws,
mark eting calls, customer acquisition or success, and post-pur chase support. 
 Fintech Pr oviders: As most of them oper ate with B2B2C business model; the y requir e an
enterprise-gr ade B2C customer support. The y also r equir e B2B sales/mark eting outbound
agents for customer acquisition. Depending on their business type, most of them serve via a
platform and r equir e an onboar ding and r eactivation support agent. 
 E-Commer ce Retailers: Their service include both physical stor es as well as online sales. Both
sales channels r equir e a high-le vel str ong customer support to follo w return policies, mak e
suggestions, oﬀer alternative pr oduct fr om the inventory , check for delivery status and manage
support tick ets in collabor ation with company staﬀ. 
 
Curr ent Sales Channels  
What channels do you curr ently use for sales, and which ar e the most eﬀective?*
We alr eady have 35+ signed enterprise deals acr oss these verticals, pr oving str ong early
demand and demonstr ating that our pr oduct solves r eal, high-ur gency pr oblems. W e’re no w
expanding the pr oduct with vertical-speciﬁc capabilities, driven dir ectly b y customer needs and
ﬁeld data. 
 -The founders and initial investors ar e high-network individuals. A consider able portion of sales
come fr om r eferr als. 
 -Second most eﬀective sales method is usage of Link edin. 
-Third method would be commer cial GTM partnerships. 
 Mark eting via ads is curr ently not within our scope; ho wever it would be an essential driver after
we close the ne xt investment r ound and automate our onboar ding pr ocess. 
 
Competitive Landscape  
What is your unique competitive advantage, and who ar e your closest competitors?*
ORCHESTRA TOR PLA TFORMS: W e diﬀer entiate b y "direct-to-customer " appr oach, deep
oper ational integr ations and customer-centricity . We belie ve, most companies will have har d-
time working on pr ompts, tools, integr ations, tests etc. to ensur e well-performing agents as part
of their staﬀ. Our participation to " outcome r esponsibility " is a clear edge for service. 
 AI AGENT ONL Y COMPETIT ORS: W e emplo y a human-in-the-loop system and additional virtual
pbx softwar e that enables hybrid call center working together with humans. V oice AI Agents will
need to tr ansfer some of the live calls to humans for the for eseeable futur e. The y should also
be well-placed within the IVR system of a virtual pb x. Our telco capabilities ar e welcomed b y
enterprises who pr efer a smooth tr ansition to V oice AI Agents. 
 VOICE AI ONL Y COMPETIT ORS: W e focus on the co-work er job r ole r ather than solely a V oice AI
on the phone. The agents we belie ve should also perform complementary tasks, not limiting
themselves to phone calls; thus should become super-emplo yees. 
 The management team of our enterprise customers ar e beneﬁting fr om uniﬁed intelligence and
"Voice of Customer " analyses pr oduced fr om inter actions all acr oss business divisions. 
 
Shar e 3 e xamples of curr ent customers or pilots, and brieﬂy describe their pr oﬁle (industry ,
size, use case)  *
Easycep(r efurbished electr onics): B2C customer support, stor e hotline, surve y; Figopar a (supply
chain ﬁnancing): B2B customer r eactivation; Metr opolcar d(emplo yee beneﬁt payment): B2B
customer acquisition

How many active users do you have? (B2C)  *
12

PivotW eek Intak e Form
Areas of Support
What ar e your top 3 pain points?  
Are ther e speciﬁc ar eas wher e you need support (e.g., GTM, pr oduct, r egulatory , sales str ategy , etc.)?*
Global GTM Partnerships, Global Refer ences outside T urkey, Regulatory Support for Finance. 
 
Partner/Customer Meetings  
Indicate the type of meetings you would lik e TBDC to set up for you.*
Customer Meetings Partner Meetings
=== END OF ATTACHED DOCUMENTS ===

=== MEETING NOTES (Fireflies.ai) ===
### TBDC Pivot Founder Discussion: DRING
Notes:
## **Program Structure and Support Model**

The Toronto Business Development Center (TBDC) offers a mostly virtual expansion program with select in-person engagements designed to boost market entry and customer relationships (06:10).

- **90% Virtual, 10% In-Person Format** enables startups to handle most planning and strategy work online, reducing travel burden.  
- In-person visits are typically short, around one week, aimed at high-value customer meetings critical for closing deals and deepening market presence.  
- The program customizes support based on startup needs, covering market intelligence, ICP mapping, customer meetings, and fundraising guidance.  
- Shaunik Sachdev emphasized the flexibility to accommodate founders’ availability, enabling mostly virtual participation if preferred.

## **Company Overview and Product Differentiation**

Drink builds AI-powered autonomous teammates for digital commerce call centers, focusing on e-commerce, retail, and fintech sectors to improve customer retention and revenue (10:45).

- Their AI agents integrate deeply with enterprise systems, including CRM and communication tools, to handle tasks like ticket creation and outbound sales calls without customer-side coding.  
- Unique telecom software lets enterprises control call routing between AI agents and human staff, supporting seamless live transfers and omnichannel communication (voice and chat).  
- Drink’s solution stands out by owning outcomes rather than just providing a DIY orchestration platform, offering embedded analytics and voice-of-customer insights for enterprise leadership.  
- The product supports inbound/outbound calls, surveys, and cross-department needs with a unified intelligence platform accessible for call logs, transcripts, and sentiment analysis.

## **Market Traction and Financial Performance**

Drink has demonstrated strong growth and market validation, with expanding enterprise customers primarily in Turkey and emerging presence in EMEA countries (15:00).

- They have a **50% compounded monthly growth rate** and have processed over **50,000 real-life calls**, indicating robust usage and scalability.  
- Current revenue includes a signed Monthly Recurring Revenue (MRR) of **approximately US$50,000** from 25 signed customers, with gradual AI adoption starting from smaller pilot usage to full integration.  
- Last year’s annual revenue was around **US$11,000**, reflecting early-stage monetization with significant growth expected as enterprises scale AI usage.  
- The team has raised **US$425,000** so far and consists of **nine fully committed members**, supported by a strong advisory board in Toronto for AI and product strategy.

## **Expansion Plans and Market Fit**

Drink has validated product-market fit, especially with fintech mid-size enterprises, and is actively growing in Turkey with opportunistic expansion in Europe and beyond (23:33).

- Most business currently derives from Turkey, with customers in the Netherlands, Germany, Dominican Republic, and Singapore mainly via referrals, not planned expansions.  
- They plan to deepen AI agent capabilities in 2024, including compliance agents for fintech, complex multi-channel workflows, and on-premises deployment with more emotionally responsive agents.  
- The vision is to achieve **$1 million Monthly Recurring Revenue by 2027**, with headquarters in Istanbul and R&D in London.  
- Challenges include fundraising difficulties in Istanbul compared to London or San Francisco, and the need for local partnerships to successfully enter Canadian and broader North American markets.

## **Fundraising Strategy and Support Needs**

Drink aims to raise a new funding round of **US$1.2 to US$1.5 million** starting in late Q3 2024 to accelerate growth and market penetration (32:10).

- Current investors include private network individuals who participated in earlier rounds; the upcoming round will seek fresh investors.  
- Shaunik Sachdev identified Drink’s top priorities as **positioning and go-to-market strategy in North America, plus fundraising support**.  
- TBDC proposed providing consulting experts to help refine Drink’s North American business setup, sales approach, and fundraising strategy before direct enterprise introductions.  
- This staged support is intended to build clarity and readiness, increasing the probability of successful market entry and capital raising.

## **Operational and Visa Support**

TBDC will assist Drink with logistical and operational challenges related to Canadian market entry, including visa facilitation for founder travel (33:10).

- Shaunik confirmed TBDC’s ability to provide support letters to accelerate visa processing once Drink joins the program.  
- This support aims to ease physical presence requirements for critical in-person meetings and partnership development.  
- Drink’s willingness to travel for short periods aligns well with TBDC’s blended virtual/in-person support model for market expansion.
Action Items:
**Shaunik Sachdev**
Coordinate a follow-up internal committee review to determine how TBDC can best support Dring.ai with go-to-market strategy and fundraising advisory (31:43)
Prepare and share a proposal outlining TBDC’s support offer and next steps to Dring.ai early next week (31:43)
Provide visa support documentation to Arda Cezzar to expedite travel arrangements once program acceptance is confirmed (33:24)

**Arda Cezzar**
Share potential times and contacts for Dring.ai partners to meet with the TBDC team if required (33:01)
=== END OF MEETING NOTES ===

Preliminary Analysis:
- Company: DRING
- Country: Turkey
- Region: Europe
- Summary: DRING is an AI-powered call center solution provider for e-commerce, finance, and digital platforms. They offer integrated and compliant agentic voice AI agents across various departments, with a focus on the Turkish market and emerging presence in EMEA countries. The company shows strong potential for Canada market entry, particularly in the fintech and e-commerce sectors.
- Product: AI-powered autonomous teammates for digital commerce call centers, focusing on e-commerce, retail, and fintech sectors
- Vertical: AI
- Business Model: B2B
- GTM Motion: SaaS
- Funding Stage: Pre-seed
- Company Size: Startup
- ICP Mapping: We focus on the sectors where our founders and advisors have deep operational expertise. This expertise allows us to tailor our AI agents to domain-specific needs such as booking flows, marketing calls, customer acquisition or success, and post-purchase support. Fintech Providers: As most of them operate with B2B2C business model; they require an enterprise-grade B2C customer support. They also require B2B sales/marketing outbound agents for customer acquisition. Depending on their business type, most of them serve via a platform and require an onboarding and reactivation support agent. E-Commerce Retailers: Their service include both physical stores as well as online sales. Both sales channels require a high-level strong customer support to follow return policies, make suggestions, offer alternative product from the inventory, check for delivery status and manage support tickets in collaboration with company staff.
- Support Required: Global GTM Partnerships, Global References outside Turkey, Regulatory Support for Finance.
- Key Insights: Strong product-market fit in Turkey with potential for North American expansion; Unique AI-powered call center solution with deep enterprise integrations; Rapid growth with 50% compounded monthly growth rate and over 50,000 processed calls
2026-02-13 20:51:21.665 | INFO     | app.services.llm.deal_analysis_service:_run_scoring_rubric:270 - === SCORING RUBRIC PROMPT END ===
2026-02-13 20:51:27.341 | INFO     | app.services.llm.deal_analysis_service:_run_scoring_rubric:287 - Scoring rubric generated: fit_score=7, rubric={'product_market_fit': 8, 'canada_market_readiness': 6, 'gtm_clarity': 7, 'team_capability': 8, 'revenue_potential': 7}