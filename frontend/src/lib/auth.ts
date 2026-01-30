/**
 * Authentication API and utilities
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Types
export interface User {
  email: string;
  name: string;
  role: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token?: string;
  user?: User;
}

// Token storage
const TOKEN_KEY = "tbdc_auth_token";
const USER_KEY = "tbdc_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function setAuthData(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// API calls
async function fetchAuth<T>(
  endpoint: string, 
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };
  
  // Add auth token if available
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  
  return response.json();
}

export const authApi = {
  /**
   * Sign up a new user
   */
  async signup(email: string, password: string, name: string): Promise<AuthResponse> {
    const response = await fetchAuth<AuthResponse>("/users/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
    
    if (response.success && response.token && response.user) {
      setAuthData(response.token, response.user);
    }
    
    return response;
  },
  
  /**
   * Log in an existing user
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await fetchAuth<AuthResponse>("/users/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    
    if (response.success && response.token && response.user) {
      setAuthData(response.token, response.user);
    }
    
    return response;
  },
  
  /**
   * Log out the current user
   */
  logout(): void {
    clearAuthData();
  },
  
  /**
   * Verify if the current token is valid
   */
  async verifyToken(): Promise<{ valid: boolean; user?: User }> {
    try {
      const response = await fetchAuth<{ valid: boolean; user?: User }>("/users/verify-token", {
        method: "POST",
      });
      return response;
    } catch {
      return { valid: false };
    }
  },
  
  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    return fetchAuth<User>("/users/me");
  },
  
  /**
   * Change password
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    return fetchAuth("/users/change-password", {
      method: "POST",
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
  },
};
