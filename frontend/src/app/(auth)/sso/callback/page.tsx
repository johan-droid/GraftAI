"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2, ShieldCheck, AlertCircle } from "lucide-react";
import { useAuthContext } from "@/app/providers/auth-provider";

function SSOCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuthContext();

  useEffect(() => {
    const token = searchParams.get("token");
    const refreshToken = searchParams.get("refresh_token");
    const error = searchParams.get("error");

    if (error) {
      console.error("[SSO_CALLBACK]: Error from backend:", error);
      return;
    }

    if (token) {
      try {
        // Set cookies locally for the current domain (graftai.tech)
        // This makes them FIRST-PARTY cookies, which browsers allow.
        
        const isProd = window.location.hostname !== "localhost";
        const secureFlag = isProd ? "secure;" : "";
        const cookieBase = `path=/; samesite=lax; ${secureFlag}`;
        
        // Access Token (1 hour)
        document.cookie = `graftai_access_token=${token}; max-age=3600; ${cookieBase}`;
        
        // Refresh Token (7 days)
        if (refreshToken) {
          document.cookie = `graftai_refresh_token=${refreshToken}; max-age=604800; ${cookieBase}`;
        }

        // Generate a temporary XSRF token for the frontend
        const xsrfToken = Math.random().toString(36).substring(2) + Math.random().toString(36).substring(2);
        document.cookie = `xsrf-token=${xsrfToken}; max-age=86400; ${cookieBase}`;

        if (typeof window !== "undefined" && window.sessionStorage) {
          window.sessionStorage.setItem("graftai_access_token", token);
          if (refreshToken) {
            window.sessionStorage.setItem("graftai_refresh_token", refreshToken);
          }
        }

        console.log("[SSO_CALLBACK]: Session established. Syncing context...");

        // Clear token params from the URL to avoid token leakage in browser history.
        if (typeof window !== "undefined" && window.history?.replaceState) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
        
        // Force the AuthProvider to refresh its session from the newly set cookies/localStorage
        login(token).then(() => {
          setTimeout(() => {
            router.replace("/dashboard");
          }, 300);
        }).catch(err => {
          console.error("Failed to sync context", err);
          setTimeout(() => {
            router.replace("/dashboard");
          }, 300);
        });

      } catch (err) {
        console.error("[SSO_CALLBACK]: Failed to set session cookies:", err);
      }
    } else {
      // No token found, maybe direct access?
      console.warn("[SSO_CALLBACK]: No token found in URL.");
      router.replace("/login");
    }
  }, [searchParams, router]);

  const error = searchParams.get("error");

  return (
    <main className="app-shell flex min-h-screen flex-col items-center justify-center p-4 relative overflow-hidden bg-[#020617]">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-[400px] z-10 text-center"
      >
        <div className="mb-8 flex justify-center">
          <motion.div
            animate={{ 
              rotate: error ? 0 : 360,
              scale: [1, 1.1, 1] 
            }}
            transition={{ 
              rotate: { duration: 2, repeat: Infinity, ease: "linear" },
              scale: { duration: 1.5, repeat: Infinity }
            }}
            className={`w-20 h-20 rounded-2xl flex items-center justify-center shadow-2xl ${
              error 
              ? "bg-red-500/20 text-red-400 border border-red-500/30" 
              : "bg-gradient-to-br from-primary to-fuchsia-600 text-white"
            }`}
          >
            {error ? <AlertCircle className="w-10 h-10" /> : <ShieldCheck className="w-10 h-10" />}
          </motion.div>
        </div>

        <h1 className="text-2xl font-bold text-white mb-3 tracking-tight">
          {error ? "Authentication Failed" : "Establishing Secure Session"}
        </h1>
        
        <p className="text-slate-400 text-sm mb-8 leading-relaxed max-w-[280px] mx-auto">
          {error 
            ? "There was an error during the sign-in process. Please try again." 
            : "We're finalizing your secure connection to the GraftAI ecosystem."}
        </p>

        {!error && (
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-3 text-primary text-sm font-medium">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Verifying tokens...</span>
            </div>
            
            <div className="w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ duration: 1.5, ease: "easeInOut" }}
                className="h-full bg-primary shadow-[0_0_10px_rgba(79,70,229,0.5)]"
              />
            </div>
          </div>
        )}

        {error && (
          <button 
            onClick={() => router.replace("/login")}
            className="px-6 py-2 rounded-xl bg-slate-800 text-white text-sm hover:bg-slate-700 transition-colors"
          >
            Return to Login
          </button>
        )}
      </motion.div>
    </main>
  );
}

export default function SSOCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#020617] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    }>
      <SSOCallbackContent />
    </Suspense>
  );
}
