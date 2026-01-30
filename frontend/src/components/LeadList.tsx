"use client";

import { Lead } from "@/types/lead";
import { Search, Building2, Mail, Phone, Globe, ChevronRight, Users, ExternalLink, Loader2, ChevronLeft } from "lucide-react";
import clsx from "clsx";

interface LeadListProps {
  leads: Lead[];
  selectedLeadId: string | null;
  onSelectLead: (lead: Lead) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  isLoading?: boolean;
  onFetchUrl?: (url: string) => void;
  isFetchingUrl?: boolean;
  // Pagination props
  currentPage?: number;
  totalCount?: number;
  perPage?: number;
  hasMoreRecords?: boolean;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  onGoToPage?: (page: number) => void;
}

// Helper to check if string looks like a URL
function isValidUrl(str: string): boolean {
  const trimmed = str.trim();
  if (!trimmed) return false;
  
  // Check for common URL patterns
  const urlPattern = /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
  return urlPattern.test(trimmed);
}

export function LeadList({
  leads,
  selectedLeadId,
  onSelectLead,
  searchQuery,
  onSearchChange,
  isLoading = false,
  onFetchUrl,
  isFetchingUrl = false,
  currentPage = 1,
  totalCount = 0,
  perPage = 100,
  hasMoreRecords = false,
  onNextPage,
  onPrevPage,
  onGoToPage,
}: LeadListProps) {
  const totalPages = Math.ceil(totalCount / perPage) || 1;
  const filteredLeads = leads.filter((lead) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    const fullName = `${lead.First_Name || ""} ${lead.Last_Name || ""}`.toLowerCase();
    const company = (lead.Company || "").toLowerCase();
    const email = (lead.Email || "").toLowerCase();
    return fullName.includes(query) || company.includes(query) || email.includes(query);
  });

  const showUrlOption = searchQuery && filteredLeads.length === 0 && isValidUrl(searchQuery);

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-emerald-50 to-white">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-lg bg-emerald-100">
            <Users className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Leads</h2>
            <p className="text-xs text-gray-500">
              {totalCount > 0 ? (
                <>Showing {((currentPage - 1) * perPage) + 1}-{Math.min(currentPage * perPage, totalCount)} of {totalCount}</>
              ) : (
                <>{leads.length} leads</>
              )}
            </p>
          </div>
        </div>
        
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, company, or email..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl 
                     focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                     placeholder:text-gray-400 bg-white"
          />
        </div>
      </div>

      {/* Lead List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          // Loading skeletons
          <div className="p-2 space-y-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="p-4 rounded-xl animate-pulse">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gray-200" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredLeads.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            {showUrlOption ? (
              // URL detected - show fetch option
              <>
                <div className="p-4 rounded-full bg-blue-100 mb-4">
                  <Globe className="w-8 h-8 text-blue-500" />
                </div>
                <h3 className="text-sm font-medium text-gray-900 mb-1">No matching leads</h3>
                <p className="text-xs text-gray-500 mb-4">
                  This looks like a website URL. Would you like to fetch company information?
                </p>
                <button
                  onClick={() => onFetchUrl?.(searchQuery)}
                  disabled={isFetchingUrl}
                  className={clsx(
                    "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all",
                    "bg-blue-600 text-white hover:bg-blue-700",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {isFetchingUrl ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Fetching...
                    </>
                  ) : (
                    <>
                      <ExternalLink className="w-4 h-4" />
                      Fetch Website Data
                    </>
                  )}
                </button>
              </>
            ) : (
              // Regular empty state
              <>
                <div className="p-4 rounded-full bg-gray-100 mb-4">
                  <Search className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-sm font-medium text-gray-900 mb-1">No leads found</h3>
                <p className="text-xs text-gray-500">
                  {searchQuery
                    ? "Try adjusting your search query"
                    : "No leads available at the moment"}
                </p>
              </>
            )}
          </div>
        ) : (
          // Lead items
          <div className="p-2 space-y-1">
            {filteredLeads.map((lead, index) => (
              <LeadItem
                key={lead.id}
                lead={lead}
                isSelected={selectedLeadId === lead.id}
                onClick={() => onSelectLead(lead)}
                index={index}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination Controls */}
      {totalCount > perPage && !searchQuery && (
        <div className="border-t border-gray-200 bg-white p-3">
          <div className="flex items-center justify-between">
            {/* Previous Button */}
            <button
              onClick={onPrevPage}
              disabled={currentPage <= 1 || isLoading}
              className={clsx(
                "flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                currentPage <= 1 || isLoading
                  ? "text-gray-300 cursor-not-allowed"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <ChevronLeft className="w-4 h-4" />
              Prev
            </button>

            {/* Page Info */}
            <div className="flex items-center gap-1">
              {/* Quick page buttons */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => onGoToPage?.(pageNum)}
                    disabled={isLoading}
                    className={clsx(
                      "w-8 h-8 rounded-lg text-sm font-medium transition-all",
                      currentPage === pageNum
                        ? "bg-emerald-500 text-white"
                        : "text-gray-600 hover:bg-gray-100"
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            {/* Next Button */}
            <button
              onClick={onNextPage}
              disabled={!hasMoreRecords || isLoading}
              className={clsx(
                "flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                !hasMoreRecords || isLoading
                  ? "text-gray-300 cursor-not-allowed"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface LeadItemProps {
  lead: Lead;
  isSelected: boolean;
  onClick: () => void;
  index: number;
}

function LeadItem({ lead, isSelected, onClick, index }: LeadItemProps) {
  const fullName = [lead.First_Name, lead.Last_Name].filter(Boolean).join(" ") || "Unknown";
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const statusColors: Record<string, string> = {
    "New": "bg-blue-100 text-blue-700",
    "Contacted": "bg-yellow-100 text-yellow-700",
    "Qualified": "bg-emerald-100 text-emerald-700",
    "Converted": "bg-purple-100 text-purple-700",
    "Lost": "bg-gray-100 text-gray-600",
  };

  const statusColor = statusColors[lead.Lead_Status || ""] || "bg-gray-100 text-gray-600";

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left p-3 rounded-xl transition-all duration-200 group",
        "hover:bg-gray-50 active:scale-[0.99]",
        isSelected
          ? "bg-emerald-50 border border-emerald-200 shadow-sm"
          : "border border-transparent"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div
          className={clsx(
            "w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium shrink-0",
            isSelected
              ? "bg-emerald-500 text-white"
              : "bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600"
          )}
        >
          {initials}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-gray-900 truncate">{fullName}</span>
            {lead.Lead_Status && (
              <span className={clsx("px-1.5 py-0.5 text-[10px] font-medium rounded-full", statusColor)}>
                {lead.Lead_Status}
              </span>
            )}
          </div>

          {lead.Company && (
            <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
              <Building2 className="w-3 h-3" />
              <span className="truncate">{lead.Company}</span>
            </div>
          )}

          <div className="flex items-center gap-3 text-xs text-gray-400">
            {lead.Email && (
              <div className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                <span className="truncate max-w-[120px]">{lead.Email}</span>
              </div>
            )}
            {/* {lead.Website && (
              <div className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
              </div>
            )}
            {lead.Phone && (
              <div className="flex items-center gap-1">
                <Phone className="w-3 h-3" />
              </div>
            )} */}
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight
          className={clsx(
            "w-4 h-4 shrink-0 transition-transform",
            isSelected ? "text-emerald-500 translate-x-1" : "text-gray-300 group-hover:text-gray-400"
          )}
        />
      </div>
    </button>
  );
}
