"use client";

import { useState, useEffect } from "react";
import { X, Save, RotateCcw, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import clsx from "clsx";
import { settingsApi, PromptsData } from "@/lib/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [analysisPrompt, setAnalysisPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"system" | "analysis">("system");

  // Load prompts when modal opens
  useEffect(() => {
    if (isOpen) {
      loadPrompts();
    }
  }, [isOpen]);

  const loadPrompts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await settingsApi.getPrompts();
      setSystemPrompt(data.system_prompt);
      setAnalysisPrompt(data.analysis_prompt);
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
      await settingsApi.updatePrompts({
        system_prompt: systemPrompt,
        analysis_prompt: analysisPrompt,
      });
      setSuccess("Prompts saved successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save prompts");
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Are you sure you want to reset prompts to defaults? This cannot be undone.")) {
      return;
    }
    
    setIsResetting(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await settingsApi.resetPrompts();
      setSystemPrompt(data.system_prompt);
      setAnalysisPrompt(data.analysis_prompt);
      setSuccess("Prompts reset to defaults!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset prompts");
    } finally {
      setIsResetting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 px-6">
            <button
              onClick={() => setActiveTab("system")}
              className={clsx(
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                activeTab === "system"
                  ? "border-emerald-500 text-emerald-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              System Prompt
            </button>
            <button
              onClick={() => setActiveTab("analysis")}
              className={clsx(
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                activeTab === "analysis"
                  ? "border-emerald-500 text-emerald-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              Analysis Prompt
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
              </div>
            ) : (
              <>
                {/* System Prompt Tab */}
                {activeTab === "system" && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        System Prompt
                      </label>
                      <p className="text-xs text-gray-500 mb-3">
                        This prompt sets the context and role for the LLM when analyzing leads.
                        It defines who the AI is and how it should behave.
                      </p>
                      <textarea
                        value={systemPrompt}
                        onChange={(e) => setSystemPrompt(e.target.value)}
                        className="w-full h-80 p-4 text-sm font-mono border border-gray-300 rounded-xl 
                                   focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                                   resize-none"
                        placeholder="Enter system prompt..."
                      />
                    </div>
                  </div>
                )}

                {/* Analysis Prompt Tab */}
                {activeTab === "analysis" && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Analysis Prompt Template
                      </label>
                      <p className="text-xs text-gray-500 mb-3">
                        This template is used for each lead analysis. Use <code className="bg-gray-100 px-1 rounded">{"{lead_data}"}</code> as 
                        a placeholder for the lead information. The response format should define the expected JSON structure.
                      </p>
                      <textarea
                        value={analysisPrompt}
                        onChange={(e) => setAnalysisPrompt(e.target.value)}
                        className="w-full h-80 p-4 text-sm font-mono border border-gray-300 rounded-xl 
                                   focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                                   resize-none"
                        placeholder="Enter analysis prompt template..."
                      />
                    </div>
                  </div>
                )}

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
              Reset to Defaults
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
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
