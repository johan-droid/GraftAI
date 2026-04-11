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
        const restoreSession = async (accessToken: string, refreshToken?: string) => {
          setStatus("Restoring your session...");
          const response = await fetch("/api/auth/restore", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json",
            },
            credentials: "include",
            body: JSON.stringify({
              access_token: accessToken,
              refresh_token: refreshToken,
              redirect_to: redirectTo,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
          }

          const data = await response.json();
          if (data.access_token) {
            if (typeof window !== "undefined") {
              window.localStorage.setItem("token", data.access_token);
              window.localStorage.setItem("graftai_access_token", data.access_token);
              sessionStorage.setItem("token", data.access_token);
              sessionStorage.setItem("graftai_access_token", data.access_token);
            }
          }
          return data;
        };

        if (accessToken) {
          try {
            await restoreSession(accessToken, refreshToken ?? undefined);
            setStatus("Login successful! Redirecting...");
            sessionStorage.removeItem("oauth_in_progress");
            safeReplace(redirectTo);
            return;
          } catch (err) {
            console.error("Session restore failed", err);
            setStatus("Failed to restore session. Redirecting to login...");
            setTimeout(() => safeReplace("/login"), 2000);
            return;
          }
        }

        if (code && state) {
          setStatus("Authenticating with OAuth provider...");

          const callbackPath = composeEndpoint("/auth/sso/callback", true);
          const response = await fetch(
            `${callbackPath}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
            {
              method: "GET",
              headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
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
            try {
              await restoreSession(data.token.access_token, data.token.refresh_token);
              setStatus("Login successful! Redirecting to dashboard...");
              safeReplace(data.redirect_to || "/dashboard");
              return;
            } catch (err) {
              console.error("Session restore failed", err);
              setStatus("Authentication failed. Redirecting to login...");
              setTimeout(() => safeReplace("/login"), 2000);
              return;
            }
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
