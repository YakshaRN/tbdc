// AI-generated analysis for a lead
export interface LeadAnalysis {
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
  likely_icp_canada?: string;
  fit_score?: number;
  fit_assessment?: string;
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

export interface Lead {
  id: string;
  First_Name?: string;
  Last_Name: string;
  Email?: string;
  Phone?: string;
  Mobile?: string;
  Company?: string;
  Title?: string;
  Industry?: string;
  Lead_Source?: string;
  Lead_Status?: string;
  Website?: string;
  Description?: string;
  Street?: string;
  City?: string;
  State?: string;
  Zip_Code?: string;
  Country?: string;
  Created_Time?: string;
  Modified_Time?: string;
  Owner?: {
    id: string;
    name: string;
    email: string;
  };
  // Additional custom fields for your dashboard
  Raise?: string;
  Verticle?: string;
  Business_Model?: string;
  Fit_Tag?: string;
  Fit_Relationship?: string;
  Typical_Customer?: string;
  Target_Group?: string;
  Questions_To_Ask?: string;
  Marketing_Material?: string;
  // Allow for any additional Zoho fields
  [key: string]: unknown;
}

// Lead with analysis data (used when fetching single lead details)
export interface LeadWithAnalysis {
  data: Lead;
  analysis?: LeadAnalysis;
  analysis_available?: boolean;
  from_cache?: boolean;
  marketing_materials?: MarketingMaterial[];
  similar_customers?: SimilarCustomer[];
}

export interface LeadListResponse {
  data: Lead[];
  page: number;
  per_page: number;
  total_count: number;
  more_records: boolean;
}

export interface LeadResponse {
  data: Lead;
  analysis?: LeadAnalysis;
  analysis_available?: boolean;
  from_cache?: boolean;
  marketing_materials?: MarketingMaterial[];
  similar_customers?: SimilarCustomer[];
}
