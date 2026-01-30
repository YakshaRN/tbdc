"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Mail, Lock, User, Loader2, AlertCircle, Eye, EyeOff } from "lucide-react";
import clsx from "clsx";

type AuthMode = "login" | "signup";

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, isLoading: authLoading } = useAuth();
  
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      let result;
      
      if (mode === "login") {
        result = await login(email, password);
      } else {
        if (!name.trim()) {
          setError("Name is required");
          setIsLoading(false);
          return;
        }
        result = await signup(email, password, name);
      }

      if (result.success) {
        router.push("/");
      } else {
        setError(result.error || "Authentication failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError(null);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <Image
              src="/tbdc-logo.png"
              alt="TBDC"
              width={200}
              height={50}
              className="h-12 w-auto"
              priority
            />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {mode === "login" ? "Welcome Back" : "Create Account"}
          </h1>
          <p className="text-gray-600 mt-1">
            {mode === "login" 
              ? "Sign in to access your dashboard" 
              : "Join TBDC to get started"}
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name field (signup only) */}
            {mode === "signup" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl 
                             focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                             placeholder:text-gray-400 transition-all"
                    required={mode === "signup"}
                  />
                </div>
              </div>
            )}

            {/* Email field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl 
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                           placeholder:text-gray-400 transition-all"
                  required
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "signup" ? "Min 6 characters" : "Enter password"}
                  className="w-full pl-11 pr-12 py-3 border border-gray-200 rounded-xl 
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                           placeholder:text-gray-400 transition-all"
                  required
                  minLength={mode === "signup" ? 6 : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className={clsx(
                "w-full py-3 px-4 rounded-xl font-medium text-white transition-all",
                "bg-gradient-to-r from-emerald-500 to-emerald-600",
                "hover:from-emerald-600 hover:to-emerald-700",
                "focus:outline-none focus:ring-2 focus:ring-emerald-500/50",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "flex items-center justify-center gap-2"
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {mode === "login" ? "Signing in..." : "Creating account..."}
                </>
              ) : (
                mode === "login" ? "Sign In" : "Create Account"
              )}
            </button>
          </form>

          {/* Toggle mode */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}
              {" "}
              <button
                onClick={toggleMode}
                className="font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
              >
                {mode === "login" ? "Sign up" : "Sign in"}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        {/* <p className="text-center text-sm text-gray-500 mt-8">
          By continuing, you agree to TBDC&apos;s Terms of Service and Privacy Policy.
        </p> */}
      </div>
    </div>
  );
}
