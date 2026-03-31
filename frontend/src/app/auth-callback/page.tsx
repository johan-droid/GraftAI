"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";
import { useAuthContext } from "@/app/providers/auth-provider";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuthContext();
  const [status, setStatus] = useState("Processing...");

  const code = searchParams.get("code");
  const state = searchParams.get("state");

  const hasFetched = useRef(false);
  
  useEffect(() => {
    const handleSync = async () => {
      if (hasFetched.current) return;
      hasFetched.current = true;
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || API_BASE_URL;
        if (code && state) {
          setStatus("Authenticating with OAuth provider...");
          
          // First, store the token from URL params to preserve it during the fetch
          // The backend will set cookies, but we also need to capture the access_token
          const response = await fetch(
            `${backendUrl}/api/v1/auth/sso/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
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
              setTimeout(() => router.replace("/login"), 1500);
              return;
            }

            throw new Error(message);
          }
          
          const data = await response.json();

          if (data.token?.access_token) {
            setStatus("Login successful! Redirecting to dashboard...");
            // Login will store the token and refresh the session
            await login(data.token.access_token);
            // Use the redirect_to from backend, default to /dashboard
            router.replace(data.redirect_to || "/dashboard");
            return;
          }
          
          if (response.status === 401 || response.status === 403) {
            setStatus("Authentication expired or not allowed. Please login again.");
            setTimeout(() => router.replace("/login"), 1000);
            return;
          }
          
          setStatus(data.detail || "Authentication failed");
          setTimeout(() => router.replace("/login"), 2000);
          return;
        } else {
          setStatus("No active session found. Redirecting to login...");
          setTimeout(() => router.replace("/login"), 2000);
        }
      } catch (err) {
        console.error("Auth callback failure:", err);
        setStatus(`Error: ${err instanceof Error ? err.message : "Authentication failed"}`);
        setTimeout(() => router.replace("/login"), 3000);
      }
    };

    handleSync();
  }, [code, state, router, login]);

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
