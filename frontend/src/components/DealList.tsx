"use client";

import { Deal } from "@/types/deal";
import { Search, Building2, DollarSign, ChevronRight, Briefcase, ChevronLeft, TrendingUp, Calendar } from "lucide-react";
import clsx from "clsx";

interface DealListProps {
  deals: Deal[];
  selectedDealId: string | null;
  onSelectDeal: (deal: Deal) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  isLoading?: boolean;
  // Pagination props
  currentPage?: number;
  totalCount?: number;
  perPage?: number;
  hasMoreRecords?: boolean;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  onGoToPage?: (page: number) => void;
}

export function DealList({
  deals,
  selectedDealId,
  onSelectDeal,
  searchQuery,
  onSearchChange,
  isLoading = false,
  currentPage = 1,
  totalCount = 0,
  perPage = 100,
  hasMoreRecords = false,
  onNextPage,
  onPrevPage,
  onGoToPage,
}: DealListProps) {
  const filteredDeals = deals.filter((deal) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    const dealName = (deal.Deal_Name || "").toLowerCase();
    const accountName = (deal.Account_Name?.name || "").toLowerCase();
    const stage = (deal.Stage || "").toLowerCase();
    const industry = (deal.Industry || "").toLowerCase();
    return dealName.includes(query) || accountName.includes(query) || stage.includes(query) || industry.includes(query);
  });

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-lg bg-blue-100">
            <Briefcase className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Applications</h2>
            <p className="text-xs text-gray-500">
              {currentPage > 1 || hasMoreRecords ? (
                <>Page {currentPage} • {((currentPage - 1) * perPage) + 1}-{((currentPage - 1) * perPage) + deals.length}{hasMoreRecords && " • More available"}</>
              ) : (
                <>{deals.length} deals</>
              )}
            </p>
          </div>
        </div>
        
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, account, or stage..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl 
                     focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500
                     placeholder:text-gray-400 bg-white"
          />
        </div>
      </div>

      {/* Deal List */}
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
        ) : filteredDeals.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <div className="p-4 rounded-full bg-gray-100 mb-4">
              <Search className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-900 mb-1">No deals found</h3>
            <p className="text-xs text-gray-500">
              {searchQuery
                ? "Try adjusting your search query"
                : "No deals available at the moment"}
            </p>
          </div>
        ) : (
          // Deal items
          <div className="p-2 space-y-1">
            {filteredDeals.map((deal, index) => (
              <DealItem
                key={deal.id}
                deal={deal}
                isSelected={selectedDealId === deal.id}
                onClick={() => onSelectDeal(deal)}
                index={index}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination Controls */}
      {(hasMoreRecords || currentPage > 1) && !searchQuery && (
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
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">Page {currentPage}</span>
              {hasMoreRecords && (
                <span className="text-gray-400">• More available</span>
              )}
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

interface DealItemProps {
  deal: Deal;
  isSelected: boolean;
  onClick: () => void;
  index: number;
}

function DealItem({ deal, isSelected, onClick, index }: DealItemProps) {
  const dealName = deal.Deal_Name || "Unknown Deal";
  const accountName = deal.Account_Name?.name || "Unknown Account";
  const industry = deal.Industry || "";
  
  // Use deal name initials for avatar
  const initials = dealName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  // Stage colors
  const stageColors: Record<string, string> = {
    "Qualification": "bg-yellow-100 text-yellow-700",
    "Needs Analysis": "bg-orange-100 text-orange-700",
    "Value Proposition": "bg-blue-100 text-blue-700",
    "Proposal/Price Quote": "bg-purple-100 text-purple-700",
    "Negotiation/Review": "bg-indigo-100 text-indigo-700",
    "Closed Won": "bg-emerald-100 text-emerald-700",
    "Closed Lost": "bg-red-100 text-red-700",
  };

  const stageColor = stageColors[deal.Stage || ""] || "bg-gray-100 text-gray-600";

  // Format amount
  const formatAmount = (amount?: number) => {
    if (!amount) return null;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left p-3 rounded-xl transition-all duration-200 group",
        "hover:bg-gray-50 active:scale-[0.99]",
        isSelected
          ? "bg-blue-50 border border-blue-200 shadow-sm"
          : "border border-transparent"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-3">
        {/* Avatar - Deal initials */}
        <div
          className={clsx(
            "w-10 h-10 rounded-lg flex items-center justify-center text-sm font-medium shrink-0",
            isSelected
              ? "bg-blue-500 text-white"
              : "bg-gradient-to-br from-blue-100 to-blue-200 text-blue-700"
          )}
        >
          {initials}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Deal Name - Primary */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-gray-900 truncate">{dealName}</span>
            {deal.Stage && (
              <span className={clsx("px-1.5 py-0.5 text-[10px] font-medium rounded-full shrink-0", stageColor)}>
                {deal.Stage}
              </span>
            )}
          </div>

          {/* Account Name - Secondary */}
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
            <Building2 className="w-3 h-3" />
            <span className="truncate">{accountName}</span>
          </div>

          {/* Industry and Amount */}
          <div className="flex items-center gap-3 text-xs text-gray-400">
            {industry && (
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                <span className="truncate max-w-[100px]">{industry}</span>
              </div>
            )}
            {deal.Amount && (
              <div className="flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                <span>{formatAmount(deal.Amount)}</span>
              </div>
            )}
            {deal.Modified_Time && (
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(deal.Modified_Time)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight
          className={clsx(
            "w-4 h-4 shrink-0 transition-transform",
            isSelected ? "text-blue-500 translate-x-1" : "text-gray-300 group-hover:text-gray-400"
          )}
        />
      </div>
    </button>
  );
}
