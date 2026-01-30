"use client";

import { Lead, LeadAnalysis, MarketingMaterial, SimilarCustomer } from "@/types/lead";
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
  Mail,
  Phone,
  ExternalLink,
  Copy,
  CheckCircle2,
  Lightbulb,
  Zap,
  Target,
  RefreshCcw,
  Info,
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

interface LeadDetailProps {
  lead: Lead | null;
  analysis?: LeadAnalysis | null;
  marketingMaterials?: MarketingMaterial[];
  similarCustomers?: SimilarCustomer[];
  isLoading?: boolean;
  isAnalysisLoading?: boolean;
  isReevaluating?: boolean;
  onReevaluate?: () => void;
}

export function LeadDetail({ 
  lead, 
  analysis, 
  marketingMaterials = [],
  similarCustomers = [],
  isLoading = false, 
  isAnalysisLoading = false,
  isReevaluating = false,
  onReevaluate,
}: LeadDetailProps) {
  if (isLoading) {
    return <LeadDetailSkeleton />;
  }

  if (!lead) {
    return <EmptyState />;
  }

  const fullName = [lead.First_Name, lead.Last_Name].filter(Boolean).join(" ") || "Unknown";

  // Get fit score label and color
  const getFitScoreDisplay = (score?: number) => {
    if (score === undefined) return null;
    if (score >= 8) return { label: "Strong Fit", color: "bg-emerald-100 text-emerald-700" };
    if (score >= 5) return { label: "Moderate Fit", color: "bg-yellow-100 text-yellow-700" };
    return { label: "Weak Fit", color: "bg-red-100 text-red-700" };
  };

  const fitScoreDisplay = getFitScoreDisplay(analysis?.fit_score);
  
  // Check if we have analysis data or if it's still loading
  const hasAnalysis = analysis && Object.keys(analysis).length > 0;

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-xl font-semibold shadow-lg shadow-emerald-200">
            {fullName
              .split(" ")
              .map((n) => n[0])
              .join("")
              .toUpperCase()
              .slice(0, 2)}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-gray-900">{fullName}</h1>
              {/* Info Icon with Hover Tooltip */}
              <LeadInfoTooltip lead={lead} />
            </div>
            {lead.Title && lead.Company && (
              <p className="text-gray-600">
                {lead.Title} at <span className="font-medium">{lead.Company}</span>
              </p>
            )}
            {!lead.Title && lead.Company && (
              <p className="text-gray-600 flex items-center gap-1.5">
                <Building2 className="w-4 h-4" />
                {lead.Company}
              </p>
            )}
            <div className="flex items-center gap-4 mt-3">
              {lead.Email && <ContactBadge icon={Mail} value={lead.Email} copyable />}
              {lead.Phone && <ContactBadge icon={Phone} value={lead.Phone} copyable />}
              {lead.Website && (
                <a
                  href={lead.Website.startsWith("http") ? lead.Website : `https://${lead.Website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-emerald-600 hover:text-emerald-700"
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
                  "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white",
                  "hover:from-emerald-600 hover:to-emerald-700 shadow-md hover:shadow-lg",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md"
                )}
                title="Regenerate AI analysis for this lead"
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
            {lead.Lead_Status && (
              <div className="px-3 py-1.5 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
                {lead.Lead_Status}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="p-6 grid grid-cols-12 gap-6">
        {/* Summary Section - Spans 8 columns */}
        <div className="col-span-8 space-y-6">
          {/* Summary Card - Modern redesign */}
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-white/20 backdrop-blur">
                  <Layers className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white text-lg">Company Overview</h3>
                  <p className="text-emerald-100 text-xs">AI-powered analysis</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              {isAnalysisLoading ? (
                <div className="space-y-6">
                  {/* Summary skeleton */}
                  <div className="space-y-2">
                    <div className="h-5 bg-gray-200 rounded w-full skeleton" />
                    <div className="h-5 bg-gray-200 rounded w-4/5 skeleton" />
                    <div className="h-5 bg-gray-200 rounded w-3/5 skeleton" />
                  </div>
                  {/* Tags skeleton */}
                  <div className="flex flex-wrap gap-2">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="h-8 bg-gray-100 rounded-full w-24 skeleton" />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* AI Summary - Hero section */}
                  {analysis?.summary && (
                    <div className="relative">
                      <div className="absolute -left-3 top-0 bottom-0 w-1 bg-gradient-to-b from-emerald-400 to-teal-400 rounded-full" />
                      <p className="text-gray-700 leading-relaxed pl-3 text-[15px]">
                        {analysis.summary}
                      </p>
                    </div>
                  )}
                  
                  {/* Product Description */}
                  {analysis?.product_description && analysis.product_description !== "Unclear from site" && (
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

                  {/* Company Tags - Pill style */}
                  <div className="flex flex-wrap gap-2">
                    <CompanyTag 
                      label="Country" 
                      value={analysis?.country || lead.Country} 
                      colorClass="bg-blue-50 text-blue-700 border-blue-200"
                      icon={MapPin}
                    />
                    <CompanyTag 
                      label="Stage" 
                      value={analysis?.raise_stage || lead.Raise} 
                      colorClass="bg-amber-50 text-amber-700 border-amber-200"
                      icon={TrendingUp}
                    />
                    <CompanyTag 
                      label="Vertical" 
                      value={analysis?.vertical || lead.Verticle || lead.Industry} 
                      colorClass="bg-purple-50 text-purple-700 border-purple-200"
                      icon={Layers}
                    />
                    <CompanyTag 
                      label="Model" 
                      value={analysis?.business_model || lead.Business_Model} 
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

                  {/* ICP Canada - Highlighted */}
                  {analysis?.likely_icp_canada && (
                    <div className="p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-cyan-50 rounded-xl border border-emerald-200">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white shrink-0">
                          <Target className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-emerald-600 uppercase tracking-wider mb-1">Likely ICP in Canada</p>
                          <p className="text-sm text-gray-800 font-medium">{analysis.likely_icp_canada}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Key Insights - Show loading or insights */}
          {(isAnalysisLoading || (analysis?.key_insights && analysis.key_insights.length > 0)) && (
            <DetailCard title="Key Insights" icon={Lightbulb} accentColor="purple">
              {isAnalysisLoading ? (
                <ul className="space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-200 skeleton flex-shrink-0 mt-0.5" />
                      <div className="flex-1 h-4 bg-gray-200 rounded skeleton" />
                    </li>
                  ))}
                </ul>
              ) : (
                <ul className="space-y-2">
                  {analysis?.key_insights?.map((insight, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <CheckCircle2 className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              )}
            </DetailCard>
          )}

          {/* Two Column Grid for Questions and Marketing */}
          <div className="grid grid-cols-2 gap-6">
            {/* Questions to Ask - Uses analysis data when available */}
            <DetailCard title="Questions to Ask Your Lead" icon={MessageCircleQuestion}>
              <div className="space-y-3">
                {isAnalysisLoading ? (
                  <ul className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <div className="w-4 h-4 rounded bg-gray-200 skeleton flex-shrink-0" />
                        <div className="flex-1 space-y-1">
                          <div className="h-4 bg-gray-200 rounded skeleton" />
                          {i % 2 === 0 && <div className="h-4 bg-gray-200 rounded w-2/3 skeleton" />}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : analysis?.questions_to_ask && analysis.questions_to_ask.length > 0 ? (
                  <ul className="space-y-2">
                    {analysis.questions_to_ask.map((q, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-emerald-500 font-semibold flex-shrink-0">{i + 1}.</span>
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                ) : lead.Questions_To_Ask ? (
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {lead.Questions_To_Ask}
                  </div>
                ) : (
                  <div className="text-sm text-gray-400 italic text-center py-4">
                    No questions available
                  </div>
                )}
              </div>
            </DetailCard>

            {/* Marketing Material */}
            <DetailCard title="Marketing Material" icon={Megaphone}>
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
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg hover:bg-emerald-50 transition-colors group"
                      >
                        <span className="text-sm text-gray-700 truncate flex-1 group-hover:text-emerald-700">
                          {material.title}
                        </span>
                        <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-emerald-600 flex-shrink-0" />
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
        </div>

        {/* Right Column - Spans 4 columns */}
        <div className="col-span-4 space-y-6">
          {/* Fit Assessment - Uses analysis fit_score when available */}
          <DetailCard title="Fit Assessment" icon={Tag}>
            {isAnalysisLoading ? (
              <div className="space-y-4">
                <div>
                  <div className="h-3 bg-gray-200 rounded w-16 skeleton mb-2" />
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gray-200 skeleton" />
                    <div className="h-6 bg-gray-200 rounded-full w-20 skeleton" />
                  </div>
                </div>
                <div>
                  <div className="h-3 bg-gray-200 rounded w-12 skeleton mb-2" />
                  <div className="h-8 bg-gray-200 rounded-lg w-24 skeleton" />
                </div>
                <div>
                  <div className="h-3 bg-gray-200 rounded w-20 skeleton mb-2" />
                  <div className="h-8 bg-gray-200 rounded-lg w-28 skeleton" />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Fit Score from Analysis */}
                {analysis?.fit_score !== undefined && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fit Score
                    </label>
                    <div className="mt-2 flex items-center gap-3">
                      <div className={clsx(
                        "w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold",
                        analysis.fit_score >= 8 ? "bg-emerald-100 text-emerald-600" :
                        analysis.fit_score >= 5 ? "bg-yellow-100 text-yellow-600" :
                        "bg-red-100 text-red-600"
                      )}>
                        {analysis.fit_score}
                      </div>
                      {fitScoreDisplay && (
                        <span className={clsx("px-2 py-1 rounded-full text-xs font-medium", fitScoreDisplay.color)}>
                          {fitScoreDisplay.label}
                        </span>
                      )}
                    </div>
                    {/* Fit Assessment Text */}
                    {analysis?.fit_assessment && (
                      <p className="mt-3 text-sm text-gray-600 leading-relaxed">
                        {analysis.fit_assessment}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </DetailCard>

          {/* Typical Customer/TG - Uses analysis data when available */}
          <DetailCard title="Typical Customer / TG" icon={Users}>
            {isAnalysisLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <div className="h-4 bg-gray-200 rounded w-32 skeleton mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-full skeleton mb-1" />
                    <div className="h-3 bg-gray-200 rounded w-2/3 skeleton" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Customer Profile Info */}
                {/* {(analysis?.company_size || analysis?.region || analysis?.likely_icp_canada) && (
                  <div className="space-y-2">
                    {analysis?.likely_icp_canada && (
                      <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                        <label className="text-xs font-medium text-emerald-600 block mb-1">
                          Likely ICP in Canada
                        </label>
                        <p className="text-sm text-gray-700">{analysis.likely_icp_canada}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-2">
                      {analysis?.company_size && (
                        <div className="p-2 bg-gray-50 rounded-lg">
                          <label className="text-xs font-medium text-gray-500 block mb-0.5">
                            Company Size
                          </label>
                          <p className="text-sm text-gray-700">{analysis.company_size}</p>
                        </div>
                      )}
                      {analysis?.region && (
                        <div className="p-2 bg-gray-50 rounded-lg">
                          <label className="text-xs font-medium text-gray-500 block mb-0.5">
                            Region
                          </label>
                          <p className="text-sm text-gray-700">{analysis.region}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )} */}

                {/* Similar Customers - Top 3 from LLM */}
                {similarCustomers && similarCustomers.length > 0 && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Similar Companies (Potential Customers)
                    </label>
                    <div className="space-y-2">
                      {similarCustomers.map((customer, index) => (
                        <div 
                          key={index} 
                          className="p-3 bg-blue-50 rounded-lg border border-blue-100 hover:border-blue-200 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-900">
                                  {customer.name}
                                </span>
                                {customer.industry && (
                                  <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">
                                    {customer.industry}
                                  </span>
                                )}
                              </div>
                              {customer.description && (
                                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                  {customer.description}
                                </p>
                              )}
                              {customer.why_similar && (
                                <p className="text-xs text-blue-600 mt-1 italic">
                                  {customer.why_similar}
                                </p>
                              )}
                            </div>
                            {customer.website && (
                              <a
                                href={customer.website.startsWith('http') ? customer.website : `https://${customer.website}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1.5 rounded-lg hover:bg-blue-100 transition-colors flex-shrink-0"
                                title="Visit website"
                              >
                                <ExternalLink className="w-3.5 h-3.5 text-blue-500" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Legacy fields from Zoho */}
                {(lead.Typical_Customer || lead.Target_Group) && (
                  <div className="space-y-2 pt-2 border-t border-gray-100">
                    {lead.Typical_Customer && (
                      <div className="p-2 bg-gray-50 rounded-lg">
                        <label className="text-xs font-medium text-gray-500 block mb-0.5">
                          Typical Customer (Zoho)
                        </label>
                        <p className="text-sm text-gray-700">{lead.Typical_Customer}</p>
                      </div>
                    )}
                    {lead.Target_Group && (
                      <div className="p-2 bg-gray-50 rounded-lg">
                        <label className="text-xs font-medium text-gray-500 block mb-0.5">
                          Target Group (Zoho)
                        </label>
                        <p className="text-sm text-gray-700">{lead.Target_Group}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Empty state */}
                {!analysis?.company_size && !analysis?.region && !analysis?.likely_icp_canada && 
                 !similarCustomers?.length && !lead.Typical_Customer && !lead.Target_Group && (
                  <div className="text-sm text-gray-400 italic text-center py-4">
                    Customer profile not available
                  </div>
                )}
              </div>
            )}
          </DetailCard>

          {/* Address */}
          {/* {(lead.Street || lead.City || lead.State || lead.Country || analysis?.country) && (
            <DetailCard title="Address" icon={MapPin}>
              <div className="text-sm text-gray-700">
                {lead.Street && <p>{lead.Street}</p>}
                {(lead.City || lead.State || lead.Zip_Code) && (
                  <p>
                    {[lead.City, lead.State, lead.Zip_Code].filter(Boolean).join(", ")}
                  </p>
                )}
                {(lead.Country || analysis?.country) && (
                  <p className="font-medium">{lead.Country || analysis?.country}</p>
                )}
              </div>
            </DetailCard>
          )} */}
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

interface SummaryItemProps {
  label: string;
  value?: string | null;
  icon: React.ComponentType<{ className?: string }>;
}

function SummaryItem({ label, value, icon: Icon }: SummaryItemProps) {
  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
      <div className="p-2 rounded-lg bg-white border border-gray-100">
        <Icon className="w-4 h-4 text-gray-400" />
      </div>
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
        <p className="text-sm font-medium text-gray-900 mt-0.5">{value || "—"}</p>
      </div>
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
  if (!value) return null;
  
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

interface ContactBadgeProps {
  icon: React.ComponentType<{ className?: string }>;
  value: string;
  copyable?: boolean;
}

function ContactBadge({ icon: Icon, value, copyable }: ContactBadgeProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="inline-flex items-center gap-1.5 text-sm text-gray-600 group">
      <Icon className="w-4 h-4 text-gray-400" />
      <span className="max-w-[180px] truncate">{value}</span>
      {copyable && (
        <button
          onClick={handleCopy}
          className="p-1 rounded hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Copy to clipboard"
        >
          {copied ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          ) : (
            <Copy className="w-3.5 h-3.5 text-gray-400" />
          )}
        </button>
      )}
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
}

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  );
}

interface LeadInfoTooltipProps {
  lead: Lead;
}

function LeadInfoTooltip({ lead }: LeadInfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const hasInfo = lead.Lead_Source || lead.Industry || lead.Owner?.name || lead.Created_Time || lead.Modified_Time;

  if (!hasInfo) return null;

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      <button
        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
        aria-label="View lead information"
      >
        <Info className="w-5 h-5" />
      </button>

      {/* Tooltip */}
      {isVisible && (
        <div className="absolute left-0 top-full mt-2 z-50 w-72 bg-white rounded-xl shadow-xl border border-gray-200 p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Arrow */}
          <div className="absolute -top-2 left-4 w-4 h-4 bg-white border-l border-t border-gray-200 transform rotate-45" />
          
          <div className="relative">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-emerald-500" />
              Lead Information
            </h4>
            <div className="space-y-2">
              {lead.Lead_Source && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Lead Source</span>
                  <span className="text-xs font-medium text-gray-900">{lead.Lead_Source}</span>
                </div>
              )}
              {lead.Industry && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Industry</span>
                  <span className="text-xs font-medium text-gray-900">{lead.Industry}</span>
                </div>
              )}
              {lead.Owner?.name && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Owner</span>
                  <span className="text-xs font-medium text-gray-900">{lead.Owner.name}</span>
                </div>
              )}
              {lead.Created_Time && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Created</span>
                  <span className="text-xs font-medium text-gray-900">
                    {new Date(lead.Created_Time).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              )}
              {lead.Modified_Time && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Last Modified</span>
                  <span className="text-xs font-medium text-gray-900">
                    {new Date(lead.Modified_Time).toLocaleDateString("en-US", {
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
          <Users className="w-10 h-10 text-gray-300" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Select a Lead</h3>
        <p className="text-gray-500">
          Choose a lead from the list on the left to view their details, qualification status, and
          marketing materials.
        </p>
      </div>
    </div>
  );
}

function LeadDetailSkeleton() {
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
              <div className="h-5 bg-gray-100 rounded w-36" />
              <div className="h-5 bg-gray-100 rounded w-28" />
            </div>
          </div>
        </div>
      </div>

      {/* Content skeleton */}
      <div className="p-6 grid grid-cols-12 gap-6">
        <div className="col-span-8 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-48" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-32" />
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-5 h-40" />
            <div className="bg-white rounded-2xl border border-gray-200 p-5 h-40" />
          </div>
        </div>
        <div className="col-span-4 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-36" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-36" />
          <div className="bg-white rounded-2xl border border-gray-200 p-5 h-48" />
        </div>
      </div>
    </div>
  );
}
