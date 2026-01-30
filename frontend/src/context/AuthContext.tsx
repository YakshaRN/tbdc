"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User, authApi, getStoredUser, getStoredToken, clearAuthData } from "@/lib/auth";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (email: string, password: string, name: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getStoredToken();
      const storedUser = getStoredUser();
      
      if (token && storedUser) {
        // Verify token is still valid
        try {
          const { valid, user: verifiedUser } = await authApi.verifyToken();
          if (valid && verifiedUser) {
            setUser(verifiedUser);
          } else {
            clearAuthData();
          }
        } catch {
          // Token invalid, clear storage
          clearAuthData();
        }
      }
      
      setIsLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password);
      
      if (response.success && response.user) {
        setUser(response.user);
        return { success: true };
      }
      
      return { success: false, error: response.message || "Login failed" };
    } catch (err) {
      return { 
        success: false, 
        error: err instanceof Error ? err.message : "Login failed" 
      };
    }
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    try {
      const response = await authApi.signup(email, password, name);
      
      if (response.success && response.user) {
        setUser(response.user);
        return { success: true };
      }
      
      return { success: false, error: response.message || "Signup failed" };
    } catch (err) {
      return { 
        success: false, 
        error: err instanceof Error ? err.message : "Signup failed" 
      };
    }
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        isLoading, 
        isAuthenticated: !!user,
        login, 
        signup, 
        logout 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
