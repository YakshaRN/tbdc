import { Lead, LeadListResponse, LeadResponse } from "@/types/lead";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

// Website data response type
export interface WebsiteData {
  success: boolean;
  url: string;
  original_url?: string;
  error?: string;
  company_name?: string;
  title?: string;
  description?: string;
  domain?: string;
  keywords?: string[];
  email?: string;
  phone?: string;
  address?: string;
  social_links?: Record<string, string>;
  logo_url?: string;
}

export const webApi = {
  /**
   * Fetch company data from a website URL
   */
  async fetchWebsiteData(url: string): Promise<WebsiteData> {
    return fetchApi<WebsiteData>(`/web/fetch?url=${encodeURIComponent(url)}`);
  },

  /**
   * Validate if a string is a valid URL
   */
  async validateUrl(url: string): Promise<{ is_valid: boolean; normalized_url?: string }> {
    return fetchApi(`/web/validate?url=${encodeURIComponent(url)}`);
  },
};

export const leadsApi = {
  /**
   * Fetch all leads with pagination
   */
  async getLeads(params?: {
    page?: number;
    per_page?: number;
    sort_by?: string;
    sort_order?: "asc" | "desc";
    fields?: string;
  }): Promise<LeadListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.per_page) searchParams.set("per_page", params.per_page.toString());
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.sort_order) searchParams.set("sort_order", params.sort_order);
    if (params?.fields) searchParams.set("fields", params.fields);

    const query = searchParams.toString();
    return fetchApi<LeadListResponse>(`/leads/${query ? `?${query}` : ""}`);
  },

  /**
   * Fetch a single lead by ID
   */
  async getLead(id: string): Promise<LeadResponse> {
    return fetchApi<LeadResponse>(`/leads/${id}`);
  },

  /**
   * Reevaluate a lead - regenerate analysis (ignore cache)
   */
  async reevaluateLead(id: string): Promise<LeadResponse> {
    return fetchApi<LeadResponse>(`/leads/${id}?refresh_analysis=true`);
  },

  /**
   * Search leads
   */
  async searchLeads(params: {
    email?: string;
    phone?: string;
    company?: string;
    criteria?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ data: Lead[]; info: Record<string, unknown> }> {
    const searchParams = new URLSearchParams();
    
    if (params.email) searchParams.set("email", params.email);
    if (params.phone) searchParams.set("phone", params.phone);
    if (params.company) searchParams.set("company", params.company);
    if (params.criteria) searchParams.set("criteria", params.criteria);
    if (params.page) searchParams.set("page", params.page.toString());
    if (params.per_page) searchParams.set("per_page", params.per_page.toString());

    return fetchApi(`/leads/search/?${searchParams.toString()}`);
  },

  /**
   * Create a new lead
   */
  async createLead(leadData: Partial<Lead>): Promise<LeadResponse> {
    return fetchApi<LeadResponse>("/leads/", {
      method: "POST",
      body: JSON.stringify(leadData),
    });
  },

  /**
   * Update an existing lead
   */
  async updateLead(id: string, leadData: Partial<Lead>): Promise<LeadResponse> {
    return fetchApi<LeadResponse>(`/leads/${id}`, {
      method: "PUT",
      body: JSON.stringify(leadData),
    });
  },

  /**
   * Delete a lead
   */
  async deleteLead(id: string): Promise<{ message: string; id: string }> {
    return fetchApi(`/leads/${id}`, {
      method: "DELETE",
    });
  },
};

// Settings/Prompts types
export interface PromptsData {
  system_prompt: string;
  analysis_prompt: string;
}

export interface PromptUpdateResponse {
  success: boolean;
  message: string;
  system_prompt: string;
  analysis_prompt: string;
}

export const settingsApi = {
  /**
   * Get current LLM prompts
   */
  async getPrompts(): Promise<PromptsData> {
    return fetchApi<PromptsData>("/settings/prompts");
  },

  /**
   * Update LLM prompts
   */
  async updatePrompts(data: Partial<PromptsData>): Promise<PromptUpdateResponse> {
    return fetchApi<PromptUpdateResponse>("/settings/prompts", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /**
   * Reset prompts to defaults
   */
  async resetPrompts(): Promise<PromptUpdateResponse> {
    return fetchApi<PromptUpdateResponse>("/settings/prompts/reset", {
      method: "POST",
    });
  },
};

export { ApiError };
