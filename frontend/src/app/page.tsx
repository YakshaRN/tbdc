"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { LeadList, LeadDetail, DealList, DealDetail, Header, WebsitePreview, SettingsModal, TabType } from "@/components";
import { Lead, LeadAnalysis, MarketingMaterial, SimilarCustomer } from "@/types/lead";
import { Deal, DealAnalysis, MarketingMaterial as DealMarketingMaterial, SimilarCustomer as DealSimilarCustomer } from "@/types/deal";
import { leadsApi, dealsApi, webApi, WebsiteData } from "@/lib/api";
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
  const [isDealsLoading, setIsDealsLoading] = useState(false);
  const [isDealsRefreshing, setIsDealsRefreshing] = useState(false);
  
  // Deals pagination state
  const [dealsCurrentPage, setDealsCurrentPage] = useState(1);
  const [dealsTotalCount, setDealsTotalCount] = useState(0);
  const [dealsHasMoreRecords, setDealsHasMoreRecords] = useState(false);
  const DEALS_PER_PAGE = 100;
  
  // ==================== SHARED STATE ====================
  const [error, setError] = useState<string | null>(null);
  
  // Website scraping state (leads only)
  const [websiteData, setWebsiteData] = useState<WebsiteData | null>(null);
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  
  // Settings modal state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  // ==================== LEADS FUNCTIONS ====================
  const fetchLeads = useCallback(async (page: number = 1, showRefreshing = false) => {
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
  }, [selectedLead]);

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
  const fetchDeals = useCallback(async (page: number = 1, showRefreshing = false) => {
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
  }, [selectedDeal]);

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

  // Website scraping functions (leads only)
  const handleFetchUrl = async (url: string) => {
    setIsFetchingUrl(true);
    setWebsiteData(null);
    setSelectedLead(null);
    setSelectedLeadAnalysis(null);
    setSelectedLeadMaterials([]);
    setError(null);

    try {
      const data = await webApi.fetchWebsiteData(url);
      setWebsiteData(data);
      
      if (!data.success) {
        setError(data.error || "Failed to fetch website data");
      }
    } catch (err) {
      console.error("Failed to fetch website:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch website");
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const handleClearWebsiteData = () => {
    setWebsiteData(null);
    setLeadSearchQuery("");
  };

  const handleWebsiteEvaluate = (
    lead: Lead,
    analysis: LeadAnalysis,
    materials: MarketingMaterial[],
    customers: SimilarCustomer[]
  ) => {
    setWebsiteData(null);
    setSelectedLead(lead);
    setSelectedLeadAnalysis(analysis);
    setSelectedLeadMaterials(materials);
    setSelectedLeadSimilarCustomers(customers);
    setIsLeadAnalysisLoading(false);
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
                onSelectLead={(lead) => {
                  setWebsiteData(null);
                  handleSelectLead(lead);
                }}
                searchQuery={leadSearchQuery}
                onSearchChange={(query) => {
                  setLeadSearchQuery(query);
                  if (!query) {
                    setWebsiteData(null);
                  }
                }}
                isLoading={isLeadsLoading}
                onFetchUrl={handleFetchUrl}
                isFetchingUrl={isFetchingUrl}
                currentPage={leadsCurrentPage}
                totalCount={leadsTotalCount}
                perPage={LEADS_PER_PAGE}
                hasMoreRecords={leadsHasMoreRecords}
                onNextPage={() => leadsHasMoreRecords && fetchLeads(leadsCurrentPage + 1)}
                onPrevPage={() => leadsCurrentPage > 1 && fetchLeads(leadsCurrentPage - 1)}
                onGoToPage={(page) => fetchLeads(page)}
              />
            </div>

            {/* Right Panel - Lead Detail or Website Preview */}
            <div className="flex-1 overflow-hidden">
              {websiteData ? (
                <WebsitePreview 
                  data={websiteData}
                  onClose={handleClearWebsiteData}
                  onEvaluate={handleWebsiteEvaluate}
                />
              ) : (
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
              )}
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
                onSearchChange={setDealSearchQuery}
                isLoading={isDealsLoading}
                currentPage={dealsCurrentPage}
                totalCount={dealsTotalCount}
                perPage={DEALS_PER_PAGE}
                hasMoreRecords={dealsHasMoreRecords}
                onNextPage={() => dealsHasMoreRecords && fetchDeals(dealsCurrentPage + 1)}
                onPrevPage={() => dealsCurrentPage > 1 && fetchDeals(dealsCurrentPage - 1)}
                onGoToPage={(page) => fetchDeals(page)}
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
