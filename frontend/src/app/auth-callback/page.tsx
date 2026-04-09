"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { composeEndpoint } from "@/lib/api-client";

function AuthCallbackInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Processing...");

  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const accessToken = searchParams.get("at") || searchParams.get("access_token");
  const refreshToken = searchParams.get("rt") || searchParams.get("refresh_token");
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const safeReplace = (path: string) => {
    if (typeof window !== "undefined") {
      window.location.replace(path);
    }
  };

  const hasFetched = useRef(false);
  
  useEffect(() => {
    const handleSync = async () => {
      if (hasFetched.current) return;
      hasFetched.current = true;
      try {
        if (accessToken) {
          setStatus("Completing SSO login...");

          window.sessionStorage.setItem("token", accessToken);
          window.localStorage.setItem("token", accessToken);
          window.sessionStorage.setItem("graftai_access_token", accessToken);
          window.localStorage.setItem("graftai_access_token", accessToken);
          if (refreshToken) {
            window.sessionStorage.setItem("refresh_token", refreshToken);
            window.localStorage.setItem("refresh_token", refreshToken);
            window.sessionStorage.setItem("graftai_refresh_token", refreshToken);
            window.localStorage.setItem("graftai_refresh_token", refreshToken);
          }

          setStatus("Login successful! Redirecting...");
          sessionStorage.removeItem("oauth_in_progress");
          safeReplace(redirectTo);
          return;
        }

        if (code && state) {
          setStatus("Authenticating with OAuth provider...");
          
          // First, store the token from URL params to preserve it during the fetch
          // The backend will set cookies, but we also need to capture the access_token
          const callbackPath = composeEndpoint("/auth/sso/callback", true);
          const response = await fetch(
            `${callbackPath}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
            {
              method: "GET",
              headers: { 
                "Accept": "application/json",
                "Content-Type": "application/json"
              },
              credentials: "include",
            }
          );
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const message = errorData.detail || `HTTP ${response.status}`;

            if (
              response.status === 410 ||
              /invalid or expired state/i.test(message) ||
              /oauth state/i.test(message)
            ) {
              setStatus("Session expired during OAuth. Redirecting to login...");
              sessionStorage.removeItem("oauth_in_progress");
              setTimeout(() => safeReplace("/login"), 1500);
              return;
            }

            throw new Error(message);
          }
          
          const data = await response.json();

          if (data.token?.access_token) {
            setStatus("Login successful! Redirecting to dashboard...");
            window.sessionStorage.setItem("token", data.token.access_token);
            window.localStorage.setItem("token", data.token.access_token);
            window.sessionStorage.setItem("graftai_access_token", data.token.access_token);
            window.localStorage.setItem("graftai_access_token", data.token.access_token);
            if (data.token.refresh_token) {
              window.sessionStorage.setItem("refresh_token", data.token.refresh_token);
              window.localStorage.setItem("refresh_token", data.token.refresh_token);
              window.sessionStorage.setItem("graftai_refresh_token", data.token.refresh_token);
              window.localStorage.setItem("graftai_refresh_token", data.token.refresh_token);
            }
            // Use the redirect_to from backend, default to /dashboard
            safeReplace(data.redirect_to || "/dashboard");
            return;
          }
          
          if (response.status === 401 || response.status === 403) {
            setStatus("Authentication expired or not allowed. Please login again.");
            setTimeout(() => safeReplace("/login"), 1000);
            return;
          }
          
          setStatus(data.detail || "Authentication failed");
          setTimeout(() => safeReplace("/login"), 2000);
          return;
        } else {
          setStatus("No active session found. Redirecting to login...");
          setTimeout(() => safeReplace("/login"), 2000);
        }
      } catch (err) {
        console.error("Auth callback failure:", err);
        setStatus(`Error: ${err instanceof Error ? err.message : "Authentication failed"}`);
        setTimeout(() => safeReplace("/login"), 3000);
      }
    };

    handleSync();
  }, [accessToken, code, redirectTo, refreshToken, state]);

  return (
    <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-xl dark:bg-slate-900 border border-slate-800">
      <p className="text-base text-slate-700 dark:text-slate-200">{status}</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <main className="app-shell flex min-h-screen items-center justify-center px-4 py-8 relative overflow-hidden bg-slate-950">
      {/* Background Ambience */}
      <div className="hidden md:block absolute top-0 left-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="hidden md:block absolute bottom-0 right-0 w-[400px] h-[400px] bg-fuchsia-500/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="z-10 relative">
        <Suspense fallback={
          <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-xl dark:bg-slate-900 border border-slate-800">
            <p className="text-base text-slate-700 dark:text-slate-200">Preparing secure connection...</p>
          </div>
        }>
          <AuthCallbackInner />
        </Suspense>
      </div>
    </main>
  );
}
