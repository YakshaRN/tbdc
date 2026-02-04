"use client";

import clsx from "clsx";
import { Users, Briefcase } from "lucide-react";

export type TabType = "leads" | "application";

interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  leadCount?: number;
  dealCount?: number;
}

export function TabNavigation({ 
  activeTab, 
  onTabChange, 
  leadCount = 0, 
  dealCount = 0 
}: TabNavigationProps) {
  const tabs = [
    { 
      id: "leads" as TabType, 
      label: "Leads", 
      icon: Users, 
      count: leadCount 
    },
    { 
      id: "application" as TabType, 
      label: "Application", 
      icon: Briefcase, 
      count: dealCount 
    },
  ];

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
              isActive
                ? "bg-white text-emerald-700 shadow-sm"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            )}
          >
            <Icon className="w-4 h-4" />
            <span>{tab.label}</span>
            {tab.count > 0 && (
              <span className={clsx(
                "px-1.5 py-0.5 text-xs rounded-full",
                isActive
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-gray-200 text-gray-600"
              )}>
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
