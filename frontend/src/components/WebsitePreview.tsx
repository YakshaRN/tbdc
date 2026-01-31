"use client";

import { useState } from "react";
import { WebsiteData, WebsiteAnalysisResponse, webApi } from "@/lib/api";
import {
  Globe,
  Building2,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  X,
  AlertCircle,
  Tag,
  Link2,
  Sparkles,
  Loader2,
  Target,
  Lightbulb,
  Users,
  RefreshCcw,
  Layers,
  Briefcase,
  TrendingUp,
  Zap,
  CheckCircle2,
  MessageCircleQuestion,
} from "lucide-react";
import clsx from "clsx";

interface WebsitePreviewProps {
  data: WebsiteData;
  onClose: () => void;
}

export function WebsitePreview({ data, onClose }: WebsitePreviewProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<WebsiteAnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const result = await webApi.analyzeWebsite(data);
      setAnalysisResult(result);
      if (!result.success) {
        setAnalysisError(result.error || "Analysis failed");
      }
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Failed to analyze website");
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!data.success) {
    return (
      <div className="h-full bg-gray-50 flex items-center justify-center p-8">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Failed to Fetch Website
          </h2>
          <p className="text-gray-600 mb-4">{data.error}</p>
          <p className="text-sm text-gray-500 mb-6">{data.url}</p>
          <button
            onClick={onClose}
            className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const hasSocialLinks = data.social_links && Object.keys(data.social_links).length > 0;

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            {/* Logo or Placeholder */}
            {data.logo_url ? (
              <img
                src={data.logo_url}
                alt={data.company_name || "Company"}
                className="w-16 h-16 rounded-2xl object-contain bg-gray-100 p-2"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xl font-semibold shadow-lg shadow-blue-200">
                {(data.company_name || data.domain || "?")
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
            )}

            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">
                {data.company_name || data.domain}
              </h1>
              {data.title && data.title !== data.company_name && (
                <p className="text-sm text-gray-600 mb-2">{data.title}</p>
              )}
              <a
                href={data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700"
              >
                <Globe className="w-4 h-4" />
                {data.domain}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Close preview"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Badge and Evaluate Button */}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
              Website Preview
            </span>
            <span className="text-xs text-gray-500">
              Data fetched from website - not a lead yet
            </span>
          </div>
          
          {/* Evaluate Button */}
          <button
            onClick={handleEvaluate}
            disabled={isAnalyzing}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all",
              isAnalyzing
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : analysisResult?.success
                  ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                  : "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700 shadow-md shadow-emerald-200"
            )}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : analysisResult?.success ? (
              <>
                <RefreshCcw className="w-4 h-4" />
                Re-evaluate
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Evaluate for Canada
              </>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Analysis Error */}
        {analysisError && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3 mb-6">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">Analysis Failed</p>
              <p className="text-sm text-red-600">{analysisError}</p>
            </div>
          </div>
        )}

        {/* Analysis Results - Match LeadDetail layout */}
        {analysisResult?.success && analysisResult.analysis && (
          <div className="grid grid-cols-12 gap-6 mb-6">
            {/* Left Column - 8 cols */}
            <div className="col-span-8 space-y-6">
              {/* Company Overview Card - Same as LeadDetail */}
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
                
                <div className="p-6 space-y-6">
                  {/* AI Summary */}
                  {analysisResult.analysis.summary && (
                    <div className="relative">
                      <div className="absolute -left-3 top-0 bottom-0 w-1 bg-gradient-to-b from-emerald-400 to-teal-400 rounded-full" />
                      <p className="text-gray-700 leading-relaxed pl-3 text-[15px]">
                        {analysisResult.analysis.summary}
                      </p>
                    </div>
                  )}
                  
                  {/* Product Description */}
                  {analysisResult.analysis.product_description && analysisResult.analysis.product_description !== "Unclear from site" && (
                    <div className="p-4 bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl border border-gray-100">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-white shrink-0">
                          <Lightbulb className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Product</p>
                          <p className="text-sm text-gray-800 font-medium">{analysisResult.analysis.product_description}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Company Tags */}
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.analysis.country && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-blue-50 text-blue-700 border-blue-200">
                        <MapPin className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Country:</span>
                        <span>{analysisResult.analysis.country}</span>
                      </div>
                    )}
                    {analysisResult.analysis.raise_stage && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-amber-50 text-amber-700 border-amber-200">
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Stage:</span>
                        <span>{analysisResult.analysis.raise_stage}</span>
                      </div>
                    )}
                    {analysisResult.analysis.vertical && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-purple-50 text-purple-700 border-purple-200">
                        <Layers className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Vertical:</span>
                        <span>{analysisResult.analysis.vertical}</span>
                      </div>
                    )}
                    {analysisResult.analysis.business_model && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-emerald-50 text-emerald-700 border-emerald-200">
                        <Briefcase className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Model:</span>
                        <span>{analysisResult.analysis.business_model}</span>
                      </div>
                    )}
                    {analysisResult.analysis.motion && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-cyan-50 text-cyan-700 border-cyan-200">
                        <Zap className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Motion:</span>
                        <span>{analysisResult.analysis.motion}</span>
                      </div>
                    )}
                    {analysisResult.analysis.company_size && (
                      <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium bg-rose-50 text-rose-700 border-rose-200">
                        <Building2 className="w-3.5 h-3.5" />
                        <span className="text-xs text-gray-500">Size:</span>
                        <span>{analysisResult.analysis.company_size}</span>
                      </div>
                    )}
                  </div>

                  {/* ICP Canada */}
                  {analysisResult.analysis.likely_icp_canada && (
                    <div className="p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-cyan-50 rounded-xl border border-emerald-200">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white shrink-0">
                          <Target className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-emerald-600 uppercase tracking-wider mb-1">Likely ICP in Canada</p>
                          <p className="text-sm text-gray-800 font-medium">{analysisResult.analysis.likely_icp_canada}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Key Insights */}
              {analysisResult.analysis.key_insights && analysisResult.analysis.key_insights.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                      <Lightbulb className="w-4 h-4" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Key Insights</h3>
                  </div>
                  <div className="p-5">
                    <ul className="space-y-2">
                      {analysisResult.analysis.key_insights.map((insight, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <CheckCircle2 className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                          <span>{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Questions to Ask */}
              {analysisResult.analysis.questions_to_ask && analysisResult.analysis.questions_to_ask.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
                      <MessageCircleQuestion className="w-4 h-4" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Questions to Ask</h3>
                  </div>
                  <div className="p-5">
                    <ul className="space-y-2">
                      {analysisResult.analysis.questions_to_ask.map((q, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-emerald-500 font-semibold flex-shrink-0">{i + 1}.</span>
                          <span>{q}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - 4 cols */}
            <div className="col-span-4 space-y-6">
              {/* Fit Assessment */}
              <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
                    <Tag className="w-4 h-4" />
                  </div>
                  <h3 className="font-semibold text-gray-900">Fit Assessment</h3>
                </div>
                <div className="p-5 space-y-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fit Score
                    </label>
                    <div className="mt-2 flex items-center gap-3">
                      <div className={clsx(
                        "w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold",
                        analysisResult.analysis.fit_score >= 8 ? "bg-emerald-100 text-emerald-600" :
                        analysisResult.analysis.fit_score >= 5 ? "bg-yellow-100 text-yellow-600" :
                        "bg-red-100 text-red-600"
                      )}>
                        {analysisResult.analysis.fit_score}
                      </div>
                      <span className={clsx(
                        "px-2 py-1 rounded-full text-xs font-medium",
                        analysisResult.analysis.fit_score >= 8 ? "bg-emerald-100 text-emerald-700" :
                        analysisResult.analysis.fit_score >= 5 ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      )}>
                        {analysisResult.analysis.fit_score >= 8 ? "Strong Fit" :
                         analysisResult.analysis.fit_score >= 5 ? "Moderate Fit" : "Weak Fit"}
                      </span>
                    </div>
                    {analysisResult.analysis.fit_assessment && (
                      <p className="mt-3 text-sm text-gray-600 leading-relaxed">
                        {analysisResult.analysis.fit_assessment}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Similar Customers */}
              {analysisResult.similar_customers && analysisResult.similar_customers.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
                      <Users className="w-4 h-4" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Typical Customer / TG</h3>
                  </div>
                  <div className="p-5">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider block mb-2">
                      Similar Companies (Potential Customers)
                    </label>
                    <div className="space-y-2">
                      {analysisResult.similar_customers.map((customer, index) => (
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
                </div>
              )}
            </div>
          </div>
        )}

        {/* Website Info Section */}
        <div className="space-y-6">
          {/* Description */}
        {data.description && (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <Building2 className="w-4 h-4" />
              </div>
              <h3 className="font-semibold text-gray-900">About</h3>
            </div>
            <div className="p-5">
              <p className="text-sm text-gray-700 leading-relaxed">
                {data.description}
              </p>
            </div>
          </div>
        )}

        {/* Contact & Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Contact Information */}
          {(data.email || data.phone || data.address) && (
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
              <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
                  <Phone className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-gray-900">Contact</h3>
              </div>
              <div className="p-5 space-y-3">
                {data.email && (
                  <a
                    href={`mailto:${data.email}`}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-emerald-50 transition-colors group"
                  >
                    <Mail className="w-4 h-4 text-gray-400 group-hover:text-emerald-600" />
                    <span className="text-sm text-gray-700 group-hover:text-emerald-700">
                      {data.email}
                    </span>
                  </a>
                )}
                {data.phone && (
                  <a
                    href={`tel:${data.phone}`}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-emerald-50 transition-colors group"
                  >
                    <Phone className="w-4 h-4 text-gray-400 group-hover:text-emerald-600" />
                    <span className="text-sm text-gray-700 group-hover:text-emerald-700">
                      {data.phone}
                    </span>
                  </a>
                )}
                {data.address && (
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-700">{data.address}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Social Links */}
          {hasSocialLinks && (
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
              <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                  <Link2 className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-gray-900">Social Links</h3>
              </div>
              <div className="p-5 space-y-2">
                {Object.entries(data.social_links!).map(([platform, url]) => (
                  <a
                    key={platform}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-purple-50 transition-colors group"
                  >
                    <span className="text-sm font-medium text-gray-700 capitalize group-hover:text-purple-700">
                      {platform}
                    </span>
                    <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-purple-600 ml-auto" />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Keywords */}
        {data.keywords && data.keywords.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
              <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                <Tag className="w-4 h-4" />
              </div>
              <h3 className="font-semibold text-gray-900">Keywords</h3>
            </div>
            <div className="p-5">
              <div className="flex flex-wrap gap-2">
                {data.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-orange-50 text-orange-700 rounded-full text-xs font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

          {/* Empty State for no data */}
          {!data.description && !data.email && !data.phone && !hasSocialLinks && (!data.keywords || data.keywords.length === 0) && !analysisResult?.success && (
            <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-gray-100 flex items-center justify-center mb-4">
                <Globe className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Limited Information Available
              </h3>
              <p className="text-sm text-gray-500">
                We couldn&apos;t extract detailed information from this website.
                <br />
                Try visiting the website directly for more details.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
