"use client";

import { useState, useEffect } from "react";
import { X, Save, RotateCcw, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import clsx from "clsx";
import { settingsApi, PromptsData } from "@/lib/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ModuleType = "leads" | "application";

// Prompt tabs per module
const LEAD_TABS = [
  { key: "system_prompt" as const, label: "System Prompt", placeholder: "{lead_data}" },
  { key: "analysis_prompt" as const, label: "Analysis Prompt", placeholder: "{lead_data}" },
];

const DEAL_TABS = [
  { key: "deal_system_prompt" as const, label: "System Prompt", placeholder: "" },
  { key: "deal_analysis_prompt" as const, label: "Analysis Prompt", placeholder: "{deal_data}" },
  { key: "deal_scoring_system_prompt" as const, label: "Scoring System Prompt", placeholder: "" },
  { key: "deal_scoring_prompt" as const, label: "Scoring Prompt", placeholder: "{deal_data}" },
];

type PromptKey = keyof PromptsData;

const PROMPT_DESCRIPTIONS: Record<PromptKey, string> = {
  system_prompt:
    "Sets the context and role for the LLM when analyzing leads. Defines who the AI is and how it should behave.",
  analysis_prompt:
    "Template used for each lead analysis. Must contain {lead_data} as a placeholder for the lead information.",
  deal_system_prompt:
    "Sets the context and role for the LLM when analyzing deals/applications. Includes pricing catalog and evaluation rules.",
  deal_analysis_prompt:
    "Template used for each deal analysis. Must contain {deal_data} as a placeholder for the deal information.",
  deal_scoring_system_prompt:
    "Dedicated prompt that defines scoring criteria and rubric for the separate scoring LLM call.",
  deal_scoring_prompt:
    "Template for the scoring call. Must contain {deal_data} and {analysis_summary} placeholders.",
};

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [prompts, setPrompts] = useState<PromptsData>({
    system_prompt: "",
    analysis_prompt: "",
    deal_system_prompt: "",
    deal_analysis_prompt: "",
    deal_scoring_system_prompt: "",
    deal_scoring_prompt: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeModule, setActiveModule] = useState<ModuleType>("leads");
  const [activePromptKey, setActivePromptKey] = useState<PromptKey>("system_prompt");

  // Load prompts when modal opens
  useEffect(() => {
    if (isOpen) {
      loadPrompts();
    }
  }, [isOpen]);

  // When switching modules, reset active tab to first prompt in that module
  useEffect(() => {
    if (activeModule === "leads") {
      setActivePromptKey("system_prompt");
    } else {
      setActivePromptKey("deal_system_prompt");
    }
  }, [activeModule]);

  const loadPrompts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await settingsApi.getPrompts();
      setPrompts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompts");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await settingsApi.updatePrompts(prompts);
      setPrompts({
        system_prompt: result.system_prompt,
        analysis_prompt: result.analysis_prompt,
        deal_system_prompt: result.deal_system_prompt,
        deal_analysis_prompt: result.deal_analysis_prompt,
        deal_scoring_system_prompt: result.deal_scoring_system_prompt,
        deal_scoring_prompt: result.deal_scoring_prompt,
      });
      setSuccess("All prompts saved successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save prompts");
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (
      !confirm(
        "Are you sure you want to reset ALL prompts (Leads + Application) to defaults? This cannot be undone."
      )
    ) {
      return;
    }

    setIsResetting(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await settingsApi.resetPrompts();
      setPrompts({
        system_prompt: data.system_prompt,
        analysis_prompt: data.analysis_prompt,
        deal_system_prompt: data.deal_system_prompt,
        deal_analysis_prompt: data.deal_analysis_prompt,
        deal_scoring_system_prompt: data.deal_scoring_system_prompt,
        deal_scoring_prompt: data.deal_scoring_prompt,
      });
      setSuccess("All prompts reset to defaults!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset prompts");
    } finally {
      setIsResetting(false);
    }
  };

  const handlePromptChange = (key: PromptKey, value: string) => {
    setPrompts((prev) => ({ ...prev, [key]: value }));
  };

  if (!isOpen) return null;

  const tabs = activeModule === "leads" ? LEAD_TABS : DEAL_TABS;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={onClose} />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative w-full max-w-5xl bg-white rounded-2xl shadow-2xl transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">LLM Prompt Settings</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Module Selector */}
          <div className="flex border-b border-gray-200 px-6 bg-gray-50">
            <button
              onClick={() => setActiveModule("leads")}
              className={clsx(
                "px-5 py-3 text-sm font-semibold transition-colors rounded-t-lg",
                activeModule === "leads"
                  ? "bg-white text-emerald-700 border border-b-0 border-gray-200 -mb-px"
                  : "text-gray-500 hover:text-gray-700"
              )}
            >
              Leads Module
            </button>
            <button
              onClick={() => setActiveModule("application")}
              className={clsx(
                "px-5 py-3 text-sm font-semibold transition-colors rounded-t-lg ml-1",
                activeModule === "application"
                  ? "bg-white text-blue-700 border border-b-0 border-gray-200 -mb-px"
                  : "text-gray-500 hover:text-gray-700"
              )}
            >
              Application Module
            </button>
          </div>

          {/* Prompt Tabs */}
          <div className="flex border-b border-gray-200 px-6 gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActivePromptKey(tab.key)}
                className={clsx(
                  "px-4 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap",
                  activePromptKey === tab.key
                    ? activeModule === "leads"
                      ? "border-emerald-500 text-emerald-600"
                      : "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
              </div>
            ) : (
              <>
                {/* Active Prompt Editor */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-sm font-medium text-gray-700">
                      {tabs.find((t) => t.key === activePromptKey)?.label || activePromptKey}
                    </label>
                    <span
                      className={clsx(
                        "px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider",
                        activeModule === "leads"
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-blue-100 text-blue-700"
                      )}
                    >
                      {activeModule === "leads" ? "Leads" : "Application"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {PROMPT_DESCRIPTIONS[activePromptKey]}
                  </p>
                  <textarea
                    value={prompts[activePromptKey]}
                    onChange={(e) => handlePromptChange(activePromptKey, e.target.value)}
                    className={clsx(
                      "w-full h-80 p-4 text-sm font-mono border rounded-xl resize-none",
                      "focus:outline-none focus:ring-2",
                      activeModule === "leads"
                        ? "border-gray-300 focus:ring-emerald-500/20 focus:border-emerald-500"
                        : "border-gray-300 focus:ring-blue-500/20 focus:border-blue-500"
                    )}
                    placeholder="Enter prompt..."
                  />
                </div>

                {/* Messages */}
                {error && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}

                {success && (
                  <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                    <p className="text-sm text-emerald-700">{success}</p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
            <button
              onClick={handleReset}
              disabled={isLoading || isResetting}
              className={clsx(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl transition-colors",
                "text-gray-600 hover:bg-gray-200",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isResetting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RotateCcw className="w-4 h-4" />
              )}
              Reset All to Defaults
            </button>

            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-200 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading || isSaving}
                className={clsx(
                  "flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl transition-colors",
                  "bg-emerald-600 text-white hover:bg-emerald-700",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Save All Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
