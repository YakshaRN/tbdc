// Revenue customer information
export interface RevenueCustomer {
  name: string;
  industry: string;
  revenue_contribution: string;
  description: string;
}

// Pricing line item for recommended services
export interface PricingLineItem {
  service_name: string;
  description: string;
  category: string; // "core_service" | "customer_meeting" | "investor_meeting" | "additional_service"
  quantity: number;
  unit_price_eur: number;
  total_price_eur: number;
}

// Pricing summary with recommended services and total cost
export interface PricingSummary {
  recommended_services: PricingLineItem[];
  total_cost_eur: number;
  pricing_notes: string[];
}

// AI-generated analysis for a deal
export interface DealAnalysis {
  company_name?: string;
  country?: string;
  region?: string;
  summary?: string;
  product_description?: string;
  vertical?: string;
  business_model?: string;
  motion?: string;
  raise_stage?: string;
  company_size?: string;
  // Revenue & Customers
  revenue_top_5_customers?: RevenueCustomer[];
  // Scoring
  scoring_rubric?: Record<string, unknown>;
  fit_score?: number;
  fit_assessment?: string;
  // ICP & Support
  icp_mapping?: string;
  likely_icp_canada?: string;
  support_required?: string;
  support_recommendations?: string[];
  // Pricing
  pricing_summary?: PricingSummary;
  // Insights
  key_insights?: string[];
  questions_to_ask?: string[];
  confidence_level?: string;
  notes?: string[];
}

// Marketing material matched by semantic similarity
export interface MarketingMaterial {
  material_id: string;
  title: string;
  link: string;
  industry?: string;
  business_topics?: string;
  similarity_score?: number;
}

// Similar customer identified by LLM analysis
export interface SimilarCustomer {
  name: string;
  description: string;
  industry?: string;
  website?: string;
  why_similar?: string;
}

export interface Deal {
  id: string;
  Deal_Name: string;
  Account_Name?: {
    id: string;
    name: string;
  };
  Contact_Name?: {
    id: string;
    name: string;
  };
  Amount?: number;
  Stage?: string;
  Closing_Date?: string;
  Probability?: number;
  Type?: string;
  Lead_Source?: string;
  Description?: string;
  Created_Time?: string;
  Modified_Time?: string;
  Owner?: {
    id: string;
    name: string;
    email: string;
  };
  // Custom fields
  Industry?: string;
  Company_Website?: string;
  Support_Required?: string;
  // Allow for any additional Zoho fields
  [key: string]: unknown;
}

// Deal with analysis data (used when fetching single deal details)
export interface DealWithAnalysis {
  data: Deal;
  analysis?: DealAnalysis;
  analysis_available?: boolean;
  from_cache?: boolean;
  marketing_materials?: MarketingMaterial[];
  similar_customers?: SimilarCustomer[];
}

export interface DealListResponse {
  data: Deal[];
  page: number;
  per_page: number;
  total_count: number;
  more_records: boolean;
}

export interface DealResponse {
  data: Deal;
  analysis?: DealAnalysis;
  analysis_available?: boolean;
  from_cache?: boolean;
  marketing_materials?: MarketingMaterial[];
  similar_customers?: SimilarCustomer[];
}
