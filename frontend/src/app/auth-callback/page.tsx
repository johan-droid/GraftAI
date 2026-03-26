"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense } from "react";
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

  useEffect(() => {
    const handleSync = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || API_BASE_URL;
        // 1. Try Better Auth Sync first if we have a session
        const { authClient } = await import("@/lib/auth-client");
        const session = await authClient.getSession();
        console.log("Better Auth Session Context:", session);
        if (session?.data) {
          setStatus("Synchronizing your account...");
          const syncResponse = await fetch(`${backendUrl}/api/v1/auth/sync`, {
            method: "POST",
            headers: {
              "Accept": "application/json",
              "Authorization": `Bearer ${session.data.session.token}`
            },
            credentials: "include",
          });
          if (syncResponse.ok) {
            router.replace("/dashboard");
            return;
          }
        }

        // 2. Fallback to legacy code/state flow if present
        if (code && state) {
          setStatus("Authenticating via legacy flow...");
          const response = await fetch(
            `${backendUrl}/api/v1/auth/sso/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
            {
              headers: { "Accept": "application/json" },
              credentials: "include",
            }
          );
          const data = await response.json();

          if (response.ok && data.token?.access_token) {
            await login(data.token.access_token);
            router.replace(data.redirect_to || "/dashboard");
            return;
          }
          setStatus(data.detail || "Authentication failed");
          return;
        }

        setStatus("No active session found. Redirecting to login...");
        setTimeout(() => router.replace("/login"), 2000);
      } catch (err) {
        console.error("Auth callback failure:", err);
        setStatus("An error occurred during authentication. Please log in again.");
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
