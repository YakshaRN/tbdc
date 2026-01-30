"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { LeadList, LeadDetail, Header, WebsitePreview, SettingsModal } from "@/components";
import { Lead, LeadAnalysis, MarketingMaterial, SimilarCustomer } from "@/types/lead";
import { leadsApi, webApi, WebsiteData } from "@/lib/api";
import { AlertCircle, RefreshCcw, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth();
  
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedLeadAnalysis, setSelectedLeadAnalysis] = useState<LeadAnalysis | null>(null);
  const [selectedLeadMaterials, setSelectedLeadMaterials] = useState<MarketingMaterial[]>([]);
  const [selectedLeadSimilarCustomers, setSelectedLeadSimilarCustomers] = useState<SimilarCustomer[]>([]);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [isReevaluating, setIsReevaluating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Website scraping state
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

  const fetchLeads = useCallback(async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      // Backend fetches ALL LinkedIn Ads leads by default (fetch_all=true)
      const response = await leadsApi.getLeads({
        sort_by: "Modified_Time",
        sort_order: "desc",
      });

      setLeads(response.data);

      // If we have a selected lead, update it with fresh data
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
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [selectedLead]);

  useEffect(() => {
    fetchLeads();
  }, []);

  const handleSelectLead = async (lead: Lead) => {
    setSelectedLead(lead);
    setSelectedLeadAnalysis(null); // Reset analysis while loading
    setSelectedLeadMaterials([]); // Reset marketing materials
    setSelectedLeadSimilarCustomers([]); // Reset similar customers
    setIsAnalysisLoading(true); // Start loading

    // Fetch full lead details with analysis
    try {
      const response = await leadsApi.getLead(lead.id);
      setSelectedLead(response.data);
      // Set analysis data if available
      if (response.analysis) {
        setSelectedLeadAnalysis(response.analysis);
      }
      // Set marketing materials if available
      if (response.marketing_materials) {
        setSelectedLeadMaterials(response.marketing_materials);
      }
      // Set similar customers if available
      if (response.similar_customers) {
        setSelectedLeadSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to fetch lead details:", err);
      // Keep the list data if detail fetch fails
    } finally {
      setIsAnalysisLoading(false); // Stop loading
    }
  };

  const handleRefresh = () => {
    fetchLeads(true);
  };

  const handleReevaluate = async () => {
    if (!selectedLead) return;

    setIsReevaluating(true);
    setError(null);

    try {
      // Call the API with refresh_analysis=true to regenerate and update cache
      const response = await leadsApi.reevaluateLead(selectedLead.id);
      
      // Update the lead and analysis with fresh data
      setSelectedLead(response.data);
      if (response.analysis) {
        setSelectedLeadAnalysis(response.analysis);
      }
      // Update marketing materials
      if (response.marketing_materials) {
        setSelectedLeadMaterials(response.marketing_materials);
      }
      // Update similar customers
      if (response.similar_customers) {
        setSelectedLeadSimilarCustomers(response.similar_customers);
      }
    } catch (err) {
      console.error("Failed to reevaluate lead:", err);
      setError(err instanceof Error ? err.message : "Failed to reevaluate lead");
    } finally {
      setIsReevaluating(false);
    }
  };

  const handleFetchUrl = async (url: string) => {
    setIsFetchingUrl(true);
    setWebsiteData(null);
    setSelectedLead(null); // Clear any selected lead
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
    setSearchQuery("");
  };

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

  if (error && leads.length === 0) {
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
              onClick={() => fetchLeads()}
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

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <Header
        onRefresh={handleRefresh}
        onSettings={() => setIsSettingsOpen(true)}
        onLogout={logout}
        isRefreshing={isRefreshing}
        leadCount={leads.length}
        userName={user?.name || "User"}
      />
      
      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Lead List */}
        <div className="w-80 xl:w-96 flex-shrink-0">
          <LeadList
            leads={leads}
            selectedLeadId={selectedLead?.id ?? null}
            onSelectLead={(lead) => {
              setWebsiteData(null); // Clear website data when selecting a lead
              handleSelectLead(lead);
            }}
            searchQuery={searchQuery}
            onSearchChange={(query) => {
              setSearchQuery(query);
              if (!query) {
                setWebsiteData(null); // Clear website data when search is cleared
              }
            }}
            isLoading={isLoading}
            onFetchUrl={handleFetchUrl}
            isFetchingUrl={isFetchingUrl}
          />
        </div>

        {/* Right Panel - Lead Detail or Website Preview */}
        <div className="flex-1 overflow-hidden">
          {websiteData ? (
            <WebsitePreview 
              data={websiteData}
              onClose={handleClearWebsiteData}
            />
          ) : (
            <LeadDetail 
              lead={selectedLead} 
              analysis={selectedLeadAnalysis}
              marketingMaterials={selectedLeadMaterials}
              similarCustomers={selectedLeadSimilarCustomers}
              isLoading={isLoading && !selectedLead}
              isAnalysisLoading={isAnalysisLoading}
              isReevaluating={isReevaluating}
              onReevaluate={handleReevaluate}
            />
          )}
        </div>
      </div>

      {/* Error Toast */}
      {error && leads.length > 0 && (
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
