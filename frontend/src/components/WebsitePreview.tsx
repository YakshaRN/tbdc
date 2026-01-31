"use client";

import { useState } from "react";
import { WebsiteData, webApi } from "@/lib/api";
import { Lead, LeadAnalysis, MarketingMaterial, SimilarCustomer } from "@/types/lead";
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
} from "lucide-react";
import clsx from "clsx";

interface WebsitePreviewProps {
  data: WebsiteData;
  onClose: () => void;
  onEvaluate?: (lead: Lead, analysis: LeadAnalysis, materials: MarketingMaterial[], customers: SimilarCustomer[]) => void;
}

export function WebsitePreview({ data, onClose, onEvaluate }: WebsitePreviewProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      // Call analyze endpoint - returns same format as LeadResponse
      const result = await webApi.analyzeWebsite(data);
      
      if (result.analysis_available && result.analysis && onEvaluate) {
        // Convert backend response to Lead type
        const websiteLead: Lead = {
          id: result.data.id || `website_${data.domain}`,
          Company: result.data.Company || data.company_name || data.domain,
          Website: result.data.Website || data.url,
          Email: result.data.Email || data.email,
          Phone: result.data.Phone || data.phone,
          First_Name: "",
          Last_Name: "",
          Lead_Source: "Website Search",
          Description: result.data.Description || data.description,
          // Flag to identify this as website data
          _source: "website",
          _logo_url: data.logo_url,
        } as Lead;
        
        // Pass results to parent
        onEvaluate(
          websiteLead,
          result.analysis,
          result.marketing_materials || [],
          result.similar_customers || []
        );
      } else {
        setAnalysisError("Analysis failed - no results returned");
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
              Data fetched from website - click Evaluate to analyze
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
                : "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700 shadow-md shadow-emerald-200"
            )}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Evaluate for Canada
              </>
            )}
          </button>
        </div>

        {/* Analysis Error */}
        {analysisError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-3 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{analysisError}</p>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
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
        {!data.description && !data.email && !data.phone && !hasSocialLinks && (!data.keywords || data.keywords.length === 0) && (
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
              Click &quot;Evaluate for Canada&quot; to get AI-powered analysis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
