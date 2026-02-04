"use client";

import { useState } from "react";
import Image from "next/image";
import { RefreshCcw, Settings, User, LogOut, ChevronDown } from "lucide-react";
import clsx from "clsx";
import { TabNavigation, TabType } from "./TabNavigation";

interface HeaderProps {
  onRefresh: () => void;
  onSettings?: () => void;
  onLogout?: () => void;
  isRefreshing?: boolean;
  leadCount?: number;
  dealCount?: number;
  userName?: string;
  activeTab?: TabType;
  onTabChange?: (tab: TabType) => void;
}

export function Header({ 
  onRefresh, 
  onSettings, 
  onLogout,
  isRefreshing = false, 
  leadCount = 0,
  dealCount = 0,
  userName = "User",
  activeTab = "leads",
  onTabChange,
}: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  // Get initials from name
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      {/* Logo and Tab Navigation */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <Image
            src="/tbdc-logo.png"
            alt="TBDC - Toronto Business Development Centre"
            width={180}
            height={40}
            className="h-10 w-auto object-contain"
            priority
          />
        </div>
        
        {/* Tab Navigation */}
        {onTabChange && (
          <TabNavigation
            activeTab={activeTab}
            onTabChange={onTabChange}
            leadCount={leadCount}
            dealCount={dealCount}
          />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className={clsx(
            "p-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
          title="Refresh leads"
        >
          <RefreshCcw
            className={clsx("w-4 h-4 text-gray-600", isRefreshing && "animate-spin")}
          />
        </button>

        {/* Settings */}
        <button
          onClick={onSettings}
          className="p-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          title="Settings"
        >
          <Settings className="w-4 h-4 text-gray-600" />
        </button>

        {/* User Profile Dropdown */}
        <div className="relative ml-2">
          <button 
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1.5 pr-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
              <span className="text-xs font-semibold text-white">{initials}</span>
            </div>
            <span className="text-sm font-medium text-gray-700 hidden sm:block max-w-[120px] truncate">
              {userName}
            </span>
            <ChevronDown className="w-4 h-4 text-gray-400 hidden sm:block" />
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <>
              {/* Backdrop */}
              <div 
                className="fixed inset-0 z-10" 
                onClick={() => setShowUserMenu(false)}
              />
              
              {/* Menu */}
              <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl border border-gray-200 shadow-lg z-20 overflow-hidden">
                <div className="p-3 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900 truncate">{userName}</p>
                  <p className="text-xs text-gray-500">User</p>
                </div>
                
                <div className="p-1">
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      onLogout?.();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
