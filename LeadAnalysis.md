
2026-02-13 21:52:31.600 | INFO     | app.services.llm.bedrock_service:analyze_lead:275 - === LEAD ANALYSIS PROMPT START ===
2026-02-13 21:52:31.600 | INFO     | app.services.llm.bedrock_service:analyze_lead:276 - System Prompt (2203 chars):
You are an expert B2B lead qualification specialist.

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
  "notes": ["Important caveats such as B2C focus, services-heavy model, regulatory friction, unclear product, or strong incumbents in Canada"]
}

Do not include explanations, markdown, or any text outside the JSON object.
2026-02-13 21:52:31.601 | INFO     | app.services.llm.bedrock_service:analyze_lead:277 - User Prompt (6289 chars):
Evaluate the following company for Canada fit.

Company Input:
- First Name: Arda
- Last Name: Cezzar
- Email: arda.cezzar@dring.ai
- Phone: +90 532 760 44 77
- Company: DringAI
- Lead Source: Linkedin Ads
- LinkedIn Profile: https://www.linkedin.com/in/ardacezzar
- Description: Are you looking to expand your business to North America?:Yes Is your company's ARR over $100,000?:Yes Do you think your product is built for the US/Canadian customer?:Yes
- Country: Türkiye
- Owner: {'name': 'Shaunik Sachdev', 'id': '5304528000000893001', 'email': 'shaunik@tbdc.com'}
- Received Responses: 1
- Designation: Co-Founder
- Layout: {'display_label': 'Horizon', 'name': 'Horizon', 'id': '5304528000035352035'}
- Last Email Received On: 2026-02-10T15:07:00+05:30
- Last Activity Time: 2026-02-10T15:07:31+05:30
- Modified By: {'name': 'Apply TBDC', 'id': '5304528000000367001', 'email': 'apply@tbdc.com'}
- Modified Time: 2026-02-10T15:07:31+05:30
- Created Time: 2026-01-07T18:21:13+05:30
- Change Log Time  s: 2026-02-10T15:07:31+05:30
- Created By: {'name': 'Apply TBDC', 'id': '5304528000000367001', 'email': 'apply@tbdc.com'}
- Full Name: Arda Cezzar
- Lead Type: Horizon
- Record Status  s: Available

=== SCRAPED LINKEDIN PROFILE ===
Arda Cezzar - DringAI | LinkedIn
Skip to main content
Sign in to view Arda’s full profile
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
Arda Cezzar
Sign in to view Arda’s full profile
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
Kadıköy, Istanbul, Türkiye
Contact Info
Sign in to view Arda’s full profile
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
2K followers
500+ connections
See your mutual connections
View mutual connections with Arda
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
Join to view profile
Message
Sign in to view Arda’s full profile
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
DringAI
Robert Koleji / Robert College
Report this profile
About
Two roads diverged in a wood, and I—
I took the one less traveled by,
And that has…
see more
Welcome back
Email or phone
Password
Show
Forgot password?
Sign in
or
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
New to LinkedIn?
Join now
Activity
Follow
Sign in to view Arda’s full profile
Arda can introduce you to 10+ people at DringAI
Email or phone
Password
Show
Forgot password?
Sign in
Sign in with Email
or
New to LinkedIn?
Join now
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
DigiHR Summit 2026’daydık.
HR teknolojilerinin geldiği noktayı, organizasyonel dönüşümü ve insan odağını merkeze alan yaklaşımları konuştuğumuz…
DigiHR Summit 2026’daydık.
HR teknolojilerinin geldiği noktayı, organizasyonel dönüşümü ve insan odağını merkeze alan yaklaşımları konuştuğumuz…
Liked by
Arda Cezzar
There's a voice AI team I talked to last month that was celebrating. Their dashboard looked great—78% containment rate, 3.8 minute average handle…
There's a voice AI team I talked to last month that was celebrating. Their dashboard looked great—78% containment rate, 3.8 minute average handle…
Liked by
Arda Cezzar
📈 This curve explains more about startups than most books ever will.
Every founder has lived some version of this line.
The early excitement, the…
📈 This curve explains more about startups than most books ever will.
Every founder has lived some version of this line.
The early excitement, the…
Liked by
Arda Cezzar
Join now to see all activity
Experience & Education
DringAI
**********
*******
****** ******* ******* * ******* *** ******** * ******** ***********
****** ******* ****
******** ** **************
****** ****** * ****** *******
-
2001
-
2006
*** ************
****** ** ******** ************** * *** *** *******
2012
-
2013
View Arda’s full experience
See their title, tenure and more.
Sign in
Welcome back
Email or phone
Password
Show
Forgot password?
Sign in
or
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
New to LinkedIn?
Join now
or
By clicking Continue to join or sign in, you agree to LinkedIn’s
User Agreement
,
Privacy Policy
, and
Cookie Policy
.
Licenses & Certifications
Product Leadership
brick institute
Issued
Jun 2023
ACP ACCREDITED COMMERCIAL PROFESSIONAL
COMMERCIAL REAL ESTATE ADVISORS LLC
Issued
Jan 2014
Courses
Advanced Broker Management Program
-
Broker Succeed
-
Maximum Results Strategies
-
RE/MAX Career
-
RE/MAX Europe Vienna Convention
-
RE/MAX Global R4 Convention
-
Residential Projects Sales Expertise
-
Languages
Turkish
Native or bilingual proficiency
English
Full professional proficiency
German
Professional working proficiency
More activity by Arda
The AI Skill Assessment Tool (AI-SAT*) that I'm working on is coming along incredibly strongly.  It will be the first ever product to actually use…
The AI Skill Assessment Tool (AI-SAT*) that I'm working on is coming along incredibly strongly.  It will be the first ever product to actually use…
Liked by
Arda Cezzar
I couldn’t agree more.
Marc Andreessen: AI coding doesn’t eliminate programm
... [truncated]
=== END OF SCRAPED LINKEDIN PROFILE ===
2026-02-13 21:52:31.601 | INFO     | app.services.llm.bedrock_service:analyze_lead:278 - === LEAD ANALYSIS PROMPT END ===
2026-02-13 21:52:31.601 | INFO     | app.services.llm.bedrock_service:analyze_lead:281 - [LeadAnalysis] LLM Call: Sending lead analysis request to Bedrock
2026-02-13 21:52:44.734 | INFO     | app.services.llm.bedrock_service:analyze_lead:289 - [LeadAnalysis] LLM Call done: Response length = 1827 chars
2026-02-13 21:52:44.735 | INFO     | app.services.llm.bedrock_service:analyze_lead:290 - [LeadAnalysis] LLM Raw Response:
{
  "company_name": "DringAI",
  "country": "Türkiye",
  "region": "Europe",
  "summary": "DringAI appears to be an AI-focused startup from Turkey, potentially in the HR tech or voice AI space. They have over $100k ARR and are actively looking to expand to North America.",
  "product_description": "Unclear from site",
  "vertical": "AI/SaaS",
  "business_model": "B2B",
  "motion": "SaaS",
  "raise_stage": "Seed",
  "company_size": "Startup",
  "likely_icp_canada": "Mid-sized companies looking to implement AI solutions in HR or customer service",
  "fit_score": 7,
  "fit_assessment": "Good potential for Canada expansion given their ARR and intent, but product clarity is needed",
  "key_insights": [
    "Over $100k ARR indicates some market traction",
    "Actively seeking North American expansion",
    "Co-founder has international experience and English proficiency",
    "Possible focus on HR tech or voice AI solutions"
  ],
  "questions_to_ask": [
    "What specific AI solutions does DringAI offer?",
    "Who are your current target customers and industries?",
    "What unique value proposition do you offer compared to North American competitors?",
    "How have you adapted your product for international markets so far?",
    "What is your current team size and do you have any North America-based employees?",
    "Do you have any early adopters or pilot customers in North America?",
    "What regulatory considerations, if any, impact your product in different markets?"
  ],
  "confidence_level": "Low",
  "notes": [
    "Product offering is unclear from available information",
    "Limited online presence makes thorough assessment difficult",
    "Potential regulatory considerations for AI products in Canada",
    "Competition from established North American AI companies may be significant"
  ]
}
2026-02-13 21:52:44.735 | INFO     | app.services.llm.bedrock_service:analyze_lead:295 - [LeadAnalysis] Parsed 17 fields from lead analysis
2026-02-13 21:52:44.735 | INFO     | app.services.llm.bedrock_service:analyze_lead:296 - [LeadAnalysis] Fields received:
  company_name: DringAI
  country: Türkiye
  region: Europe
  summary: DringAI appears to be an AI-focused startup from Turkey, potentially in the HR tech or voice AI space. They have over $100k ARR and are actively looking to expand to North America.
  product_description: Unclear from site
  vertical: AI/SaaS
  business_model: B2B
  motion: SaaS
  raise_stage: Seed
  company_size: Startup
  likely_icp_canada: Mid-sized companies looking to implement AI solutions in HR or customer service
  fit_score: 7
  fit_assessment: Good potential for Canada expansion given their ARR and intent, but product clarity is needed
  key_insights: ['Over $100k ARR indicates some market traction', 'Actively seeking North American expansion', 'Co-founder has international experience and English proficiency', 'Possible focus on HR tech or voice AI solutions']
  questions_to_ask: ['What specific AI solutions does DringAI offer?', 'Who are your current target customers and industries?', 'What unique value proposition do you offer compared to North American competitors?', 'How have you adapted your product for international markets so far?', 'What is your current team size and do you have any North America-based employees?', 'Do you have any early adopters or pilot customers in North America?', 'What regulatory considerations, if any, impact your product in different markets?']
  confidence_level: Low
  notes: ['Product offering is unclear from available information', 'Limited online presence makes thorough assessment difficult', 'Potential regulatory considerations for AI products in Canada', 'Competition from established North American AI companies may be significant']