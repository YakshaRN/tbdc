"use client";

import { Deal, DealAnalysis, MarketingMaterial, SimilarCustomer, RevenueCustomer, PricingSummary as PricingSummaryType, PricingLineItem } from "@/types/deal";
import {
  Globe,
  Building2,
  MapPin,
  TrendingUp,
  Layers,
  Briefcase,
  Tag,
  Users,
  MessageCircleQuestion,
  Megaphone,
  DollarSign,
  ExternalLink,
  Copy,
  CheckCircle2,
  Lightbulb,
  Zap,
  Target,
  RefreshCcw,
  Info,
  LifeBuoy,
  ClipboardList,
  MapPinned,
  Receipt,
  Package,
  CircleDot,
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

interface DealDetailProps {
  deal: Deal | null;
  analysis?: DealAnalysis | null;
  marketingMaterials?: MarketingMaterial[];
  similarCustomers?: SimilarCustomer[];
  isLoading?: boolean;
  isAnalysisLoading?: boolean;
  isReevaluating?: boolean;
  onReevaluate?: () => void;
}

export function DealDetail({ 
  deal, 
  analysis, 
  marketingMaterials = [],
  similarCustomers = [],
  isLoading = false, 
  isAnalysisLoading = false,
  isReevaluating = false,
  onReevaluate,
}: DealDetailProps) {
  if (isLoading) {
    return <DealDetailSkeleton />;
  }

  if (!deal) {
    return <EmptyState />;
  }

  const dealName = deal.Deal_Name || "Unknown Deal";
  const accountName = deal.Account_Name?.name || "";

  // Get fit score label and color
  const getFitScoreDisplay = (score?: number) => {
    if (score === undefined) return null;
    if (score >= 8) return { label: "Strong Fit", color: "bg-emerald-100 text-emerald-700" };
    if (score >= 5) return { label: "Moderate Fit", color: "bg-yellow-100 text-yellow-700" };
    return { label: "Weak Fit", color: "bg-red-100 text-red-700" };
  };

  const fitScoreDisplay = getFitScoreDisplay(analysis?.fit_score);
  
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

  // Format EUR currency
  const formatEUR = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Get category display label
  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      core_service: "Core Service",
      customer_meeting: "Customer Meeting",
      investor_meeting: "Investor Meeting",
      additional_service: "Additional Service",
    };
    return labels[category] || category;
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xl font-semibold shadow-lg shadow-blue-200">
            {dealName
              .split(" ")
              .map((n) => n[0])
              .join("")
              .toUpperCase()
              .slice(0, 2)}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-gray-900">{dealName}</h1>
              {/* Info Icon with Hover Tooltip */}
              <DealInfoTooltip deal={deal} />
            </div>
            {accountName && (
              <p className="text-gray-600 flex items-center gap-1.5">
                <Building2 className="w-4 h-4" />
                {accountName}
              </p>
            )}
            <div className="flex items-center gap-4 mt-3">
              {deal.Amount && (
                <div className="flex items-center gap-1.5 text-sm text-gray-600">
                  <DollarSign className="w-4 h-4 text-gray-400" />
                  <span className="font-medium">{formatAmount(deal.Amount)}</span>
                </div>
              )}
              {deal.Stage && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                  {deal.Stage}
                </span>
              )}
              {deal.Company_Website && (
                <a
                  href={deal.Company_Website.startsWith("http") ? deal.Company_Website : `https://${deal.Company_Website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700"
                >
                  <Globe className="w-4 h-4" />
                  <span>Website</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Reevaluate Button */}
            {onReevaluate && (
              <button
                onClick={onReevaluate}
                disabled={isReevaluating || isAnalysisLoading}
                className={clsx(
                  "inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all",
                  "bg-gradient-to-r from-blue-500 to-blue-600 text-white",
                  "hover:from-blue-600 hover:to-blue-700 shadow-md hover:shadow-lg",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md"
                )}
                title="Regenerate AI analysis for this deal"
              >
                <RefreshCcw className={clsx("w-4 h-4", isReevaluating && "animate-spin")} />
                {isReevaluating ? "Reevaluating..." : "Reevaluate"}
              </button>
            )}
            {analysis?.confidence_level && (
              <div className={clsx(
                "px-3 py-1.5 rounded-full text-sm font-medium",
                analysis.confidence_level === "High" ? "bg-emerald-100 text-emerald-700" :
                analysis.confidence_level === "Medium" ? "bg-yellow-100 text-yellow-700" :
                "bg-gray-100 text-gray-600"
              )}>
                {analysis.confidence_level} Confidence
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid - Two Column Layout per Wireframe */}
      <div className="p-6 grid grid-cols-12 gap-6">
        {/* Left/Middle Column - Summary, Revenue Top 5, Marketing Material */}
        <div className="col-span-7 space-y-6">
          {/* Summary Card */}
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-white/20 backdrop-blur">
                  <Layers className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white text-lg">Summary</h3>
                  <p className="text-blue-100 text-xs">AI-powered analysis</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              {isAnalysisLoading ? (
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="h-5 bg-gray-200 rounded w-full skeleton" />
                    <div className="h-5 bg-gray-200 rounded w-4/5 skeleton" />
                    <div className="h-5 bg-gray-200 rounded w-3/5 skeleton" />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="h-8 bg-gray-100 rounded-full w-24 skeleton" />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* AI Summary */}
                  {analysis?.summary && (
                    <div className="relative">
                      <div className="absolute -left-3 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-400 to-purple-400 rounded-full" />
                      <p className="text-gray-700 leading-relaxed pl-3 text-[15px]">
                        {analysis.summary}
                      </p>
                    </div>
                  )}
                  
                  {/* Product Description */}
                  {analysis?.product_description && analysis.product_description !== "Unknown" && (
                    <div className="p-4 bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl border border-gray-100">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-white shrink-0">
                          <Lightbulb className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Product</p>
                          <p className="text-sm text-gray-800 font-medium">{analysis.product_description}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Company Tags */}
                  <div className="flex flex-wrap gap-2">
                    <CompanyTag 
                      label="Country" 
                      value={analysis?.country} 
                      colorClass="bg-blue-50 text-blue-700 border-blue-200"
                      icon={MapPin}
                    />
                    <CompanyTag 
                      label="Stage" 
                      value={analysis?.raise_stage} 
                      colorClass="bg-amber-50 text-amber-700 border-amber-200"
                      icon={TrendingUp}
                    />
                    <CompanyTag 
                      label="Vertical" 
                      value={analysis?.vertical || deal.Industry} 
                      colorClass="bg-purple-50 text-purple-700 border-purple-200"
                      icon={Layers}
                    />
                    <CompanyTag 
                      label="Model" 
                      value={analysis?.business_model} 
                      colorClass="bg-emerald-50 text-emerald-700 border-emerald-200"
                      icon={Briefcase}
                    />
                    <CompanyTag 
                      label="Motion" 
                      value={analysis?.motion} 
                      colorClass="bg-cyan-50 text-cyan-700 border-cyan-200"
                      icon={Zap}
                    />
                    <CompanyTag 
                      label="Size" 
                      value={analysis?.company_size} 
                      colorClass="bg-rose-50 text-rose-700 border-rose-200"
                      icon={Building2}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Revenue from Top 5 Customers */}
          <DetailCard title="Revenue from Top 5 Customers" icon={DollarSign} accentColor="blue">
            {isAnalysisLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <div className="h-4 bg-gray-200 rounded w-32 skeleton mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-full skeleton" />
                  </div>
                ))}
              </div>
            ) : analysis?.revenue_top_5_customers && analysis.revenue_top_5_customers.length > 0 ? (
              <div className="space-y-3">
                {analysis.revenue_top_5_customers.map((customer, index) => (
                  <div 
                    key={index} 
                    className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-gray-900">{customer.name}</span>
                      {customer.industry && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                          {customer.industry}
                        </span>
                      )}
                    </div>
                    {customer.revenue_contribution && (
                      <p className="text-xs text-blue-600 font-medium">{customer.revenue_contribution}</p>
                    )}
                    {customer.description && (
                      <p className="text-xs text-gray-600 mt-1">{customer.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : similarCustomers && similarCustomers.length > 0 ? (
              // Fall back to similar customers if no revenue data
              <div className="space-y-3">
                <p className="text-xs text-gray-500 italic mb-2">Showing similar customers (revenue data not available)</p>
                {similarCustomers.slice(0, 5).map((customer, index) => (
                  <div 
                    key={index} 
                    className="p-3 bg-blue-50 rounded-lg border border-blue-100"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-semibold text-gray-900">{customer.name}</span>
                        {customer.industry && (
                          <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">
                            {customer.industry}
                          </span>
                        )}
                        {customer.description && (
                          <p className="text-xs text-gray-600 mt-1">{customer.description}</p>
                        )}
                      </div>
                      {customer.website && (
                        <a
                          href={customer.website.startsWith('http') ? customer.website : `https://${customer.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 rounded-lg hover:bg-blue-100 transition-colors flex-shrink-0"
                        >
                          <ExternalLink className="w-3.5 h-3.5 text-blue-500" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-400 italic text-center py-4">
                No customer revenue data available
              </div>
            )}
          </DetailCard>

          {/* Marketing Material to share */}
          <DetailCard title="Marketing Material to Share" icon={Megaphone} accentColor="purple">
            <div className="space-y-2">
              {isAnalysisLoading ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="p-2 bg-gray-50 rounded-lg">
                      <div className="h-4 bg-gray-200 rounded w-3/4 skeleton" />
                    </div>
                  ))}
                </div>
              ) : marketingMaterials && marketingMaterials.length > 0 ? (
                <div className="space-y-2">
                  {marketingMaterials.map((material, index) => (
                    <a
                      key={material.material_id || index}
                      href={material.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg hover:bg-purple-50 transition-colors group"
                    >
                      <span className="text-sm text-gray-700 truncate flex-1 group-hover:text-purple-700">
                        {material.title}
                      </span>
                      <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-purple-600 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-400 italic text-center py-4">
                  No marketing material available
                </div>
              )}
            </div>
          </DetailCard>
        </div>

        {/* Right Column - Scoring Rubric, ICP Mapping, Support Required */}
        <div className="col-span-5 space-y-6">
          {/* Scoring Rubric */}
          <DetailCard title="Scoring Rubric" icon={ClipboardList} accentColor="emerald">
            {isAnalysisLoading ? (
              <div className="space-y-4">
                <div>
                  <div className="h-3 bg-gray-200 rounded w-16 skeleton mb-2" />
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gray-200 skeleton" />
                    <div className="h-6 bg-gray-200 rounded-full w-20 skeleton" />
                  </div>
                </div>
                <div className="h-16 bg-gray-200 rounded-lg skeleton" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Fit Score */}
                {analysis?.fit_score !== undefined && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fit Score
                    </label>
                    <div className="mt-2 flex items-center gap-3">
                      <div className={clsx(
                        "w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold",
                        analysis.fit_score >= 8 ? "bg-emerald-100 text-emerald-600" :
                        analysis.fit_score >= 5 ? "bg-yellow-100 text-yellow-600" :
                        "bg-red-100 text-red-600"
                      )}>
                        {analysis.fit_score}
                      </div>
                      {fitScoreDisplay && (
                        <span className={clsx("px-3 py-1.5 rounded-full text-sm font-medium", fitScoreDisplay.color)}>
                          {fitScoreDisplay.label}
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Fit Assessment */}
                {analysis?.fit_assessment && (
                  <div className="p-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg border border-emerald-100">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {analysis.fit_assessment}
                    </p>
                  </div>
                )}

                {/* Key Insights */}
                {analysis?.key_insights && analysis.key_insights.length > 0 && (
                  <div className="pt-3 border-t border-gray-100">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Key Insights
                    </label>
                    <ul className="space-y-2">
                      {analysis.key_insights.slice(0, 3).map((insight, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span>{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </DetailCard>

          {/* ICP Mapping - Pricing Summary */}
          <DetailCard title="ICP Mapping" icon={MapPinned} accentColor="blue">
            {isAnalysisLoading ? (
              <div className="space-y-3">
                <div className="h-10 bg-gray-200 rounded-lg skeleton" />
                <div className="h-10 bg-gray-200 rounded-lg skeleton" />
                <div className="h-10 bg-gray-200 rounded-lg skeleton" />
                <div className="h-8 bg-gray-200 rounded-lg skeleton mt-4" />
              </div>
            ) : analysis?.pricing_summary &&
              analysis.pricing_summary.recommended_services &&
              analysis.pricing_summary.recommended_services.length > 0 ? (
              <div className="space-y-4">
                {/* Service Line Items */}
                <div className="overflow-hidden rounded-xl border border-gray-200">
                  {/* Table Header */}
                  <div className="grid grid-cols-12 gap-2 px-4 py-2.5 bg-gray-50 border-b border-gray-200">
                    <div className="col-span-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Service</div>
                    <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase tracking-wider text-center">Qty</div>
                    <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Unit Price</div>
                    <div className="col-span-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Total</div>
                  </div>
                  {/* Line Items */}
                  {analysis.pricing_summary.recommended_services.map((item, index) => {
                    const isIncluded = item.unit_price_eur === 0;
                    const categoryLabel = getCategoryLabel(item.category);
                    return (
                      <div
                        key={index}
                        className={clsx(
                          "grid grid-cols-12 gap-2 px-4 py-3 items-center",
                          index % 2 === 0 ? "bg-white" : "bg-gray-50/50",
                          index < analysis.pricing_summary!.recommended_services.length - 1 && "border-b border-gray-100"
                        )}
                      >
                        <div className="col-span-5">
                          <div className="flex items-start gap-2">
                            <CircleDot className={clsx(
                              "w-3.5 h-3.5 mt-0.5 flex-shrink-0",
                              isIncluded ? "text-emerald-400" : "text-blue-400"
                            )} />
                            <div>
                              <p className="text-sm font-medium text-gray-900 leading-tight">{item.service_name}</p>
                              <p className="text-[10px] text-gray-400 mt-0.5">{categoryLabel}</p>
                            </div>
                          </div>
                        </div>
                        <div className="col-span-2 text-sm text-gray-600 text-center">{item.quantity}</div>
                        <div className="col-span-2 text-sm text-gray-600 text-right">
                          {isIncluded ? (
                            <span className="text-emerald-600 font-medium text-xs">Included</span>
                          ) : (
                            formatEUR(item.unit_price_eur)
                          )}
                        </div>
                        <div className="col-span-3 text-sm font-medium text-right">
                          {isIncluded ? (
                            <span className="text-emerald-600 text-xs">EUR 0</span>
                          ) : (
                            <span className="text-gray-900">{formatEUR(item.total_price_eur)}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {/* Total Row */}
                  <div className="grid grid-cols-12 gap-2 px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-t-2 border-blue-200">
                    <div className="col-span-9">
                      <span className="text-sm font-bold text-gray-900">Estimated Total</span>
                    </div>
                    <div className="col-span-3 text-right">
                      <span className="text-base font-bold text-blue-700">
                        {formatEUR(analysis.pricing_summary.total_cost_eur)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Pricing Notes */}
                {analysis.pricing_summary.pricing_notes &&
                  analysis.pricing_summary.pricing_notes.length > 0 && (
                  <div className="pt-2">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Pricing Rationale
                    </label>
                    <ul className="space-y-1.5">
                      {analysis.pricing_summary.pricing_notes.map((note, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                          <span className="text-blue-400 mt-0.5 flex-shrink-0">•</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-400 italic text-center py-4">
                Pricing summary not available
              </div>
            )}
          </DetailCard>

          {/* Support Required */}
          <DetailCard title="Support Required" icon={LifeBuoy} accentColor="purple">
            {isAnalysisLoading ? (
              <div className="space-y-3">
                <div className="h-20 bg-gray-200 rounded-lg skeleton" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Support Required from Zoho */}
                {(analysis?.support_required || deal.Support_Required) && (
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
                    <p className="text-sm text-gray-800 leading-relaxed">
                      {analysis?.support_required || deal.Support_Required}
                    </p>
                  </div>
                )}

                {/* Support Recommendations from LLM */}
                {analysis?.support_recommendations && analysis.support_recommendations.length > 0 && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Recommended Support Actions
                    </label>
                    <ul className="space-y-2">
                      {analysis.support_recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <CheckCircle2 className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Notes/Caveats */}
                {analysis?.notes && analysis.notes.length > 0 && (
                  <div className="pt-3 border-t border-gray-100">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Important Notes
                    </label>
                    <ul className="space-y-1">
                      {analysis.notes.map((note, i) => (
                        <li key={i} className="text-xs text-gray-500 italic">
                          • {note}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Empty state */}
                {!analysis?.support_required && !deal.Support_Required && 
                 (!analysis?.support_recommendations || analysis.support_recommendations.length === 0) && (
                  <div className="text-sm text-gray-400 italic text-center py-4">
                    No support requirements specified
                  </div>
                )}
              </div>
            )}
          </DetailCard>
        </div>
      </div>
    </div>
  );
}

// Subcomponents

interface DetailCardProps {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  accentColor?: "emerald" | "blue" | "purple";
}

function DetailCard({ title, icon: Icon, children, accentColor = "emerald" }: DetailCardProps) {
  const accentClasses = {
    emerald: "from-emerald-500 to-emerald-600",
    blue: "from-blue-500 to-blue-600",
    purple: "from-purple-500 to-purple-600",
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
        <div className={clsx("p-2 rounded-lg bg-gradient-to-br text-white", accentClasses[accentColor])}>
          <Icon className="w-4 h-4" />
        </div>
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

interface CompanyTagProps {
  label: string;
  value?: string | null;
  colorClass: string;
  icon: React.ComponentType<{ className?: string }>;
}

function CompanyTag({ label, value, colorClass, icon: Icon }: CompanyTagProps) {
  if (!value || value === "Unknown") return null;
  
  return (
    <div className={clsx(
      "inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium transition-all hover:scale-105",
      colorClass
    )}>
      <Icon className="w-3.5 h-3.5" />
      <span className="text-xs text-gray-500">{label}:</span>
      <span>{value}</span>
    </div>
  );
}

interface DealInfoTooltipProps {
  deal: Deal;
}

function DealInfoTooltip({ deal }: DealInfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const hasInfo = deal.Lead_Source || deal.Industry || deal.Owner?.name || deal.Created_Time || deal.Closing_Date;

  if (!hasInfo) return null;

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      <button
        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
        aria-label="View deal information"
      >
        <Info className="w-5 h-5" />
      </button>

      {/* Tooltip */}
      {isVisible && (
        <div className="absolute left-0 top-full mt-2 z-50 w-72 bg-white rounded-xl shadow-xl border border-gray-200 p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="absolute -top-2 left-4 w-4 h-4 bg-white border-l border-t border-gray-200 transform rotate-45" />
          
          <div className="relative">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-blue-500" />
              Deal Information
            </h4>
            <div className="space-y-2">
              {deal.Lead_Source && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Lead Source</span>
                  <span className="text-xs font-medium text-gray-900">{deal.Lead_Source}</span>
                </div>
              )}
              {deal.Industry && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Industry</span>
                  <span className="text-xs font-medium text-gray-900">{deal.Industry}</span>
                </div>
              )}
              {deal.Probability !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Probability</span>
                  <span className="text-xs font-medium text-gray-900">{deal.Probability}%</span>
                </div>
              )}
              {deal.Owner?.name && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Owner</span>
                  <span className="text-xs font-medium text-gray-900">{deal.Owner.name}</span>
                </div>
              )}
              {deal.Closing_Date && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Closing Date</span>
                  <span className="text-xs font-medium text-gray-900">
                    {new Date(deal.Closing_Date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              )}
              {deal.Created_Time && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Created</span>
                  <span className="text-xs font-medium text-gray-900">
                    {new Date(deal.Created_Time).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md">
        <div className="mx-auto w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mb-6">
          <Briefcase className="w-10 h-10 text-gray-300" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Select an Application</h3>
        <p className="text-gray-500">
          Choose a deal from the list on the left to view its details, scoring rubric, ICP mapping, and support requirements.
        </p>
      </div>
    </div>
  );
}

function DealDetailSkeleton() {
  return (
    <div className="h-full overflow-y-auto bg-gray-50 animate-pulse">
      {/* Header skeleton */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gray-200" />
          <div className="flex-1 space-y-2">
            <div className="h-6 bg-gray-200 rounded w-48" />
            <div className="h-4 bg-gray-100 rounded w-32" />
            <div className="flex gap-4 mt-3">
              <div className="h-5 bg-gray-100 rounded w-24" />
              <div className="h-5 bg-gray-100 rounded w-20" />
            </div>
          </div>
        </div>
      </div>

      {/* Content skeleton */}
      <div className="p-6 grid grid-cols-12 gap-6">
        <div className="col-span-7 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-64" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-48" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-36" />
        </div>
        <div className="col-span-5 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-48" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-56" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-40" />
        </div>
      </div>
    </div>
  );
}
