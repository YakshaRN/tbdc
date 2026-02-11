"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { LeadList, LeadDetail, DealList, DealDetail, Header, SettingsModal, TabType } from "@/components";
import { Lead, LeadAnalysis, MarketingMaterial, SimilarCustomer } from "@/types/lead";
import { Deal, DealAnalysis, MarketingMaterial as DealMarketingMaterial, SimilarCustomer as DealSimilarCustomer } from "@/types/deal";
import { leadsApi, dealsApi, webApi } from "@/lib/api";
import { AlertCircle, RefreshCcw, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth();
  
  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>("leads");
  
  // ==================== LEADS STATE ====================
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedLeadAnalysis, setSelectedLeadAnalysis] = useState<LeadAnalysis | null>(null);
  const [selectedLeadMaterials, setSelectedLeadMaterials] = useState<MarketingMaterial[]>([]);
  const [selectedLeadSimilarCustomers, setSelectedLeadSimilarCustomers] = useState<SimilarCustomer[]>([]);
  const [isLeadAnalysisLoading, setIsLeadAnalysisLoading] = useState(false);
  const [isLeadReevaluating, setIsLeadReevaluating] = useState(false);
  const [leadSearchQuery, setLeadSearchQuery] = useState("");
  const [leadsAreFromSearch, setLeadsAreFromSearch] = useState(false);
  const [isLeadsLoading, setIsLeadsLoading] = useState(true);
  const [isLeadsRefreshing, setIsLeadsRefreshing] = useState(false);
  
  // Leads pagination state
  const [leadsCurrentPage, setLeadsCurrentPage] = useState(1);
  const [leadsTotalCount, setLeadsTotalCount] = useState(0);
  const [leadsHasMoreRecords, setLeadsHasMoreRecords] = useState(false);
  const LEADS_PER_PAGE = 100;
  
  // ==================== DEALS STATE ====================
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [selectedDealAnalysis, setSelectedDealAnalysis] = useState<DealAnalysis | null>(null);
  const [selectedDealMaterials, setSelectedDealMaterials] = useState<DealMarketingMaterial[]>([]);
  const [selectedDealSimilarCustomers, setSelectedDealSimilarCustomers] = useState<DealSimilarCustomer[]>([]);
  const [isDealAnalysisLoading, setIsDealAnalysisLoading] = useState(false);
  const [isDealReevaluating, setIsDealReevaluating] = useState(false);
  const [dealSearchQuery, setDealSearchQuery] = useState("");
  const [dealsAreFromSearch, setDealsAreFromSearch] = useState(false);
  const [isDealsLoading, setIsDealsLoading] = useState(false);
  const [isDealsRefreshing, setIsDealsRefreshing] = useState(false);
  
  // Deals pagination state
  const [dealsCurrentPage, setDealsCurrentPage] = useState(1);
  const [dealsTotalCount, setDealsTotalCount] = useState(0);
  const [dealsHasMoreRecords, setDealsHasMoreRecords] = useState(false);
  const DEALS_PER_PAGE = 100;
  
  // ==================== SHARED STATE ====================
  const [error, setError] = useState<string | null>(null);
  
  // Website URL evaluation state (leads only)
  const [isEvaluatingUrl, setIsEvaluatingUrl] = useState(false);
  
  // Settings modal state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  // ==================== LEADS FUNCTIONS ====================
  const fetchLeads = useCallback(
    async (page: number = 1, showRefreshing = false) => {
      try {
        if (showRefreshing) {
          setIsLeadsRefreshing(true);
        } else {
          setIsLeadsLoading(true);
        }
        setError(null);

        const response = await leadsApi.getLeads({
          page,
          per_page: LEADS_PER_PAGE,
          sort_by: "Modified_Time",
          sort_order: "desc",
        });

        setLeads(response.data);
        setLeadsAreFromSearch(false);
        setLeadsCurrentPage(response.page);
        setLeadsTotalCount(response.total_count);
        setLeadsHasMoreRecords(response.more_records);

        if (selectedLead) {
          const updatedLead = response.data.find((l) => l.id === selectedLead.id);
          if (updatedLead) {
            setSelectedLead(updatedLead);
          }
        }
      } catch (err) {
        console.error("Failed to fetch leads:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch leads");
      } finally {
        setIsLeadsLoading(false);
        setIsLeadsRefreshing(false);
      }
    },
    [selectedLead]
  );

  // Helper to detect if a string looks like a URL/domain
  const isUrlLike = useCallback((str: string): boolean => {
    const trimmed = str.trim();
    if (!trimmed) return false;
    const urlPattern = /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
    return urlPattern.test(trimmed);
  }, []);

  // Auto-evaluate a website URL: scrape + LLM + cache (one-shot)
  const evaluateWebsiteUrl = useCallback(
    async (url: string) => {
      setIsEvaluatingUrl(true);
      setIsLeadAnalysisLoading(true);
      setSelectedLead(null);
      setSelectedLeadAnalysis(null);
      setSelectedLeadMaterials([]);
      setSelectedLeadSimilarCustomers([]);
      setError(null);

      try {
        const result = await webApi.evaluateUrl(url);

        if (result.analysis_available && result.analysis) {
          // Build a Lead object from the response
          const websiteLead: Lead = {
            id: result.data.id || `website_${url}`,
            Company: result.data.Company || url,
            Website: result.data.Website || url,
            Email: result.data.Email || "",
            Phone: result.data.Phone || "",
            First_Name: "",
            Last_Name: "",
            Lead_Source: "Website Search",
            Description: result.data.Description || "",
            _source: "website",
            _logo_url: result.data._logo_url,
          } as Lead;

          setSelectedLead(websiteLead);
          setSelectedLeadAnalysis(result.analysis);
          setSelectedLeadMaterials(result.marketing_materials || []);
          setSelectedLeadSimilarCustomers(result.similar_customers || []);
        } else {
          setError("Website evaluation failed — no analysis returned.");
        }
      } catch (err) {
        console.error("Failed to evaluate website:", err);
        setError(err instanceof Error ? err.message : "Failed to evaluate website");
      } finally {
        setIsEvaluatingUrl(false);
        setIsLeadAnalysisLoading(false);
      }
    },
    []
  );

  // Backend-powered search across ALL leads (name, company, email, owner, etc.)
  const searchLeads = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed) {
        // If query cleared, reset to first page of normal list
        setLeadsAreFromSearch(false);
        fetchLeads(1);
        return;
      }

      // If it looks like a URL, auto-evaluate it instead of searching Zoho
      if (isUrlLike(trimmed)) {
        evaluateWebsiteUrl(trimmed);
        return;
      }

      // Avoid Zoho "Invalid query formed" for very short search terms
      if (trimmed.length < 3 && !trimmed.includes("@")) {
        setError("Please enter at least 3 characters to search leads.");
        return;
      }

      try {
        setIsLeadsLoading(true);
        setError(null);

        const params = {
          search_query: trimmed,
          page: 1,
          per_page: LEADS_PER_PAGE,
        };

        const result = await leadsApi.searchLeads(params);
        const data = (result as any).data || [];
        const info = (result as any).info || {};
        const page = info.page ?? 1;
        const perPage = info.per_page ?? LEADS_PER_PAGE;
        const moreRecords = Boolean(info.more_records);

        setLeads(data);
        setLeadsAreFromSearch(true);
        setLeadsCurrentPage(page);
        setLeadsTotalCount((page - 1) * perPage + data.length);
        setLeadsHasMoreRecords(moreRecords);
      } catch (err) {
        console.error("Failed to search leads:", err);
        setError(err instanceof Error ? err.message : "Failed to search leads");
      } finally {
        setIsLeadsLoading(false);
        setIsLeadsRefreshing(false);
      }
    },
    [fetchLeads, isUrlLike, evaluateWebsiteUrl]
  );

  // Load a specific page of search results (when leadsAreFromSearch)
  const fetchSearchLeadsPage = useCallback(
    async (page: number) => {
      const trimmed = leadSearchQuery.trim();
      if (!trimmed) return;

      try {
        setIsLeadsLoading(true);
        setError(null);

        const result = await leadsApi.searchLeads({
          search_query: trimmed,
          page,
          per_page: LEADS_PER_PAGE,
        });
        const data = (result as any).data || [];
        const info = (result as any).info || {};
        const perPage = info.per_page ?? LEADS_PER_PAGE;
        const moreRecords = Boolean(info.more_records);

        setLeads(data);
        setLeadsCurrentPage(page);
        setLeadsTotalCount((page - 1) * perPage + data.length);
        setLeadsHasMoreRecords(moreRecords);
      } catch (err) {
        console.error("Failed to fetch search page:", err);
        setError(err instanceof Error ? err.message : "Failed to load search results");
      } finally {
        setIsLeadsLoading(false);
      }
    },
    [leadSearchQuery]
  );

  const handleSelectLead = async (lead: Lead) => {
    setSelectedLead(lead);
    setSelectedLeadAnalysis(null);
    setSelectedLeadMaterials([]);
    setSelectedLeadSimilarCustomers([]);
    setIsLeadAnalysisLoading(true);

    try {
      const response = await leadsApi.getLead(lead.id);
      setSelectedLead(response.data);
      if (response.analysis) {
        setSelectedLeadAnalysis(response.analysis);
      }
      if (response.marketing_materials) {
        setSelectedLeadMaterials(response.marketing_materials);
      }
      if (response.similar_customers) {
        setSelectedLeadSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to fetch lead details:", err);
    } finally {
      setIsLeadAnalysisLoading(false);
    }
  };

  const handleLeadReevaluate = async () => {
    if (!selectedLead) return;

    setIsLeadReevaluating(true);
    setError(null);

    try {
      const response = await leadsApi.reevaluateLead(selectedLead.id);
      setSelectedLead(response.data);
      if (response.analysis) {
        setSelectedLeadAnalysis(response.analysis);
      }
      if (response.marketing_materials) {
        setSelectedLeadMaterials(response.marketing_materials);
      }
      if (response.similar_customers) {
        setSelectedLeadSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to reevaluate lead:", err);
      setError(err instanceof Error ? err.message : "Failed to reevaluate lead");
    } finally {
      setIsLeadReevaluating(false);
    }
  };

  // ==================== DEALS FUNCTIONS ====================
  const fetchDeals = useCallback(
    async (page: number = 1, showRefreshing = false) => {
      try {
        if (showRefreshing) {
          setIsDealsRefreshing(true);
        } else {
          setIsDealsLoading(true);
        }
        setError(null);

        const response = await dealsApi.getDeals({
          page,
          per_page: DEALS_PER_PAGE,
          sort_by: "Modified_Time",
          sort_order: "desc",
        });

        setDeals(response.data);
        setDealsAreFromSearch(false);
        setDealsCurrentPage(response.page);
        setDealsTotalCount(response.total_count);
        setDealsHasMoreRecords(response.more_records);

        if (selectedDeal) {
          const updatedDeal = response.data.find((d) => d.id === selectedDeal.id);
          if (updatedDeal) {
            setSelectedDeal(updatedDeal);
          }
        }
      } catch (err) {
        console.error("Failed to fetch deals:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch deals");
      } finally {
        setIsDealsLoading(false);
        setIsDealsRefreshing(false);
      }
    },
    [selectedDeal]
  );

  // Backend-powered search across ALL deals (deal name, account, contact, owner, etc.)
  const searchDeals = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed) {
        // If query cleared, reset to first page of normal list
        setDealsAreFromSearch(false);
        fetchDeals(1);
        return;
      }

      // Avoid Zoho "Invalid query formed" for very short search terms
      if (trimmed.length < 3) {
        setError("Please enter at least 3 characters to search deals.");
        return;
      }

      try {
        setIsDealsLoading(true);
        setError(null);

        const result = await dealsApi.searchDeals({
          search_query: trimmed,
          page: 1,
          per_page: DEALS_PER_PAGE,
        });
        const data = (result as any).data || [];
        const info = (result as any).info || {};
        const page = info.page ?? 1;
        const perPage = info.per_page ?? DEALS_PER_PAGE;
        const moreRecords = Boolean(info.more_records);

        setDeals(data);
        setDealsAreFromSearch(true);
        setDealsCurrentPage(page);
        setDealsTotalCount((page - 1) * perPage + data.length);
        setDealsHasMoreRecords(moreRecords);
      } catch (err) {
        console.error("Failed to search deals:", err);
        setError(err instanceof Error ? err.message : "Failed to search deals");
      } finally {
        setIsDealsLoading(false);
        setIsDealsRefreshing(false);
      }
    },
    [fetchDeals]
  );

  // Load a specific page of deal search results (when dealsAreFromSearch)
  const fetchSearchDealsPage = useCallback(
    async (page: number) => {
      const trimmed = dealSearchQuery.trim();
      if (!trimmed) return;

      try {
        setIsDealsLoading(true);
        setError(null);

        const result = await dealsApi.searchDeals({
          search_query: trimmed,
          page,
          per_page: DEALS_PER_PAGE,
        });
        const data = (result as any).data || [];
        const info = (result as any).info || {};
        const perPage = info.per_page ?? DEALS_PER_PAGE;
        const moreRecords = Boolean(info.more_records);

        setDeals(data);
        setDealsCurrentPage(page);
        setDealsTotalCount((page - 1) * perPage + data.length);
        setDealsHasMoreRecords(moreRecords);
      } catch (err) {
        console.error("Failed to fetch deal search page:", err);
        setError(err instanceof Error ? err.message : "Failed to load search results");
      } finally {
        setIsDealsLoading(false);
      }
    },
    [dealSearchQuery]
  );

  const handleSelectDeal = async (deal: Deal) => {
    setSelectedDeal(deal);
    setSelectedDealAnalysis(null);
    setSelectedDealMaterials([]);
    setSelectedDealSimilarCustomers([]);
    setIsDealAnalysisLoading(true);

    try {
      const response = await dealsApi.getDeal(deal.id);
      setSelectedDeal(response.data);
      if (response.analysis) {
        setSelectedDealAnalysis(response.analysis);
      }
      if (response.marketing_materials) {
        setSelectedDealMaterials(response.marketing_materials);
      }
      if (response.similar_customers) {
        setSelectedDealSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to fetch deal details:", err);
    } finally {
      setIsDealAnalysisLoading(false);
    }
  };

  const handleDealReevaluate = async () => {
    if (!selectedDeal) return;

    setIsDealReevaluating(true);
    setError(null);

    try {
      const response = await dealsApi.reevaluateDeal(selectedDeal.id);
      setSelectedDeal(response.data);
      if (response.analysis) {
        setSelectedDealAnalysis(response.analysis);
      }
      if (response.marketing_materials) {
        setSelectedDealMaterials(response.marketing_materials);
      }
      if (response.similar_customers) {
        setSelectedDealSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to reevaluate deal:", err);
      setError(err instanceof Error ? err.message : "Failed to reevaluate deal");
    } finally {
      setIsDealReevaluating(false);
    }
  };

  // ==================== SHARED FUNCTIONS ====================
  const handleRefresh = () => {
    if (activeTab === "leads") {
      fetchLeads(leadsCurrentPage, true);
    } else {
      fetchDeals(dealsCurrentPage, true);
    }
  };

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setError(null);
    
    // Fetch deals when switching to application tab for the first time
    if (tab === "application" && deals.length === 0 && !isDealsLoading) {
      fetchDeals();
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchLeads();
  }, []);

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-emerald-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Error state (only show if no data at all)
  const hasNoData = activeTab === "leads" ? leads.length === 0 : deals.length === 0;
  if (error && hasNoData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="space-y-3">
            <button
              onClick={() => activeTab === "leads" ? fetchLeads() : fetchDeals()}
              className="w-full px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
            >
              <RefreshCcw className="w-4 h-4" />
              Try Again
            </button>
            <p className="text-xs text-gray-500">
              Make sure your backend server is running on{" "}
              <code className="bg-gray-100 px-1.5 py-0.5 rounded">http://localhost:8000</code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const isRefreshing = activeTab === "leads" ? isLeadsRefreshing : isDealsRefreshing;

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header with Tab Navigation */}
      <Header
        onRefresh={handleRefresh}
        onSettings={() => setIsSettingsOpen(true)}
        onLogout={logout}
        isRefreshing={isRefreshing}
        leadCount={leads.length}
        dealCount={deals.length}
        userName={user?.name || "User"}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />
      
      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === "leads" ? (
          <>
            {/* Left Panel - Lead List */}
            <div className="w-80 xl:w-96 flex-shrink-0">
              <LeadList
                leads={leads}
                selectedLeadId={selectedLead?.id ?? null}
                onSelectLead={handleSelectLead}
                searchQuery={leadSearchQuery}
                onSearchChange={(query) => {
                  setLeadSearchQuery(query);

                  if (!query.trim()) {
                    // Reset to normal paginated list when search cleared
                    fetchLeads(1);
                  }
                }}
                onSearchSubmit={searchLeads}
                isLoading={isLeadsLoading}
                isEvaluatingUrl={isEvaluatingUrl}
                leadsAreFromSearch={leadsAreFromSearch}
                currentPage={leadsCurrentPage}
                totalCount={leadsTotalCount}
                perPage={LEADS_PER_PAGE}
                hasMoreRecords={leadsHasMoreRecords}
                onNextPage={() =>
                  leadsAreFromSearch
                    ? (leadsHasMoreRecords && fetchSearchLeadsPage(leadsCurrentPage + 1))
                    : (leadsHasMoreRecords && fetchLeads(leadsCurrentPage + 1))
                }
                onPrevPage={() =>
                  leadsAreFromSearch
                    ? (leadsCurrentPage > 1 && fetchSearchLeadsPage(leadsCurrentPage - 1))
                    : (leadsCurrentPage > 1 && fetchLeads(leadsCurrentPage - 1))
                }
                onGoToPage={(page) =>
                  leadsAreFromSearch ? fetchSearchLeadsPage(page) : fetchLeads(page)
                }
              />
            </div>

            {/* Right Panel - Lead Detail */}
            <div className="flex-1 overflow-hidden">
              <LeadDetail 
                lead={selectedLead} 
                analysis={selectedLeadAnalysis}
                marketingMaterials={selectedLeadMaterials}
                similarCustomers={selectedLeadSimilarCustomers}
                isLoading={isLeadsLoading && !selectedLead}
                isAnalysisLoading={isLeadAnalysisLoading}
                isReevaluating={isLeadReevaluating}
                onReevaluate={handleLeadReevaluate}
              />
            </div>
          </>
        ) : (
          <>
            {/* Left Panel - Deal List */}
            <div className="w-80 xl:w-96 flex-shrink-0">
              <DealList
                deals={deals}
                selectedDealId={selectedDeal?.id ?? null}
                onSelectDeal={handleSelectDeal}
                searchQuery={dealSearchQuery}
                onSearchChange={(query) => {
                  setDealSearchQuery(query);
                  if (!query.trim()) {
                    // Reset to normal paginated list when search cleared
                    fetchDeals(1);
                  }
                }}
                onSearchSubmit={searchDeals}
                isLoading={isDealsLoading}
                dealsAreFromSearch={dealsAreFromSearch}
                currentPage={dealsCurrentPage}
                totalCount={dealsTotalCount}
                perPage={DEALS_PER_PAGE}
                hasMoreRecords={dealsHasMoreRecords}
                onNextPage={() =>
                  dealsAreFromSearch
                    ? (dealsHasMoreRecords && fetchSearchDealsPage(dealsCurrentPage + 1))
                    : (dealsHasMoreRecords && fetchDeals(dealsCurrentPage + 1))
                }
                onPrevPage={() =>
                  dealsAreFromSearch
                    ? (dealsCurrentPage > 1 && fetchSearchDealsPage(dealsCurrentPage - 1))
                    : (dealsCurrentPage > 1 && fetchDeals(dealsCurrentPage - 1))
                }
                onGoToPage={(page) =>
                  dealsAreFromSearch ? fetchSearchDealsPage(page) : fetchDeals(page)
                }
              />
            </div>

            {/* Right Panel - Deal Detail */}
            <div className="flex-1 overflow-hidden">
              <DealDetail 
                deal={selectedDeal} 
                analysis={selectedDealAnalysis}
                marketingMaterials={selectedDealMaterials}
                similarCustomers={selectedDealSimilarCustomers}
                isLoading={isDealsLoading && !selectedDeal}
                isAnalysisLoading={isDealAnalysisLoading}
                isReevaluating={isDealReevaluating}
                onReevaluate={handleDealReevaluate}
              />
            </div>
          </>
        )}
      </div>

      {/* Error Toast */}
      {error && !hasNoData && (
        <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-xl p-4 shadow-lg flex items-center gap-3 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <div>
            <p className="text-sm font-medium text-red-800">Sync Error</p>
            <p className="text-xs text-red-600">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-400 hover:text-red-600"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
}
