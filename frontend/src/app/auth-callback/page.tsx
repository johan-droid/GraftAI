"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/api";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Processing...");

  const code = searchParams.get("code");
  const state = searchParams.get("state");

  useEffect(() => {
    if (!code || !state) {
      return;
    }

    const fetchCallback = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || API_BASE_URL;
        const response = await fetch(
          `${backendUrl}/auth/sso/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
          {
            headers: {
              "Accept": "application/json",
            },
            credentials: "include", // Keep cookies from backend for session
          }
        );
        const data = await response.json();

        if (!response.ok) {
          const errorMsg = data.detail || `Server error (${response.status})`;
          console.error("SSO Error:", data);
          setStatus(errorMsg);
          return;
        }

        if (data.token?.access_token) {
          setToken(data.token.access_token);
          const finalRedirect = data.redirect_to || "/dashboard";
          router.replace(finalRedirect);
          return;
        }

        setStatus("No access token returned from callback");
      } catch (err) {
        console.error("Fetch failure:", err);
        setStatus("Connection error: Ensure NEXT_PUBLIC_API_BASE_URL is set on Vercel.");
      }
    };

    fetchCallback();
  }, [code, state, router]);

  if (!code || !state) {
    return (
      <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-xl dark:bg-slate-900 border border-slate-800">
        <p className="text-base text-slate-700 dark:text-slate-200">Missing SSO code or state parameter</p>
      </div>
    );
  }

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
