"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";
import { composeEndpoint } from "@/lib/api-client";

/**
 * /auth-callback
 *
 * Two entry scenarios:
 *
 * 1. NextAuth flow (normal path)
 *    NextAuth handles the OAuth exchange directly — this page is NOT hit.
 *    Users land directly on `/dashboard` after sign-in.
 *
 * 2. Backend SSO redirect flow (legacy path)
 *    The backend's /api/v1/auth/{provider}/callback sends the user here with:
 *      ?access_token=...&refresh_token=...&redirect=...
 *    We call /api/auth/restore to validate and set HttpOnly cookies,
 *    then navigate to the target.
 *
 * 3. Backend code+state flow
 *    The backend sends ?code=...&state=... for SSO Enterprise flows.
 */
function AuthCallbackInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Processing your sign-in…");
  const hasFetched = useRef(false);

  const accessToken  = searchParams.get("at") || searchParams.get("access_token");
  const refreshToken = searchParams.get("rt") || searchParams.get("refresh_token");
  const redirectTo   = searchParams.get("redirect") || "/dashboard";
  const code         = searchParams.get("code");
  const state        = searchParams.get("state");

  const safeReplace = (path: string) => {
    if (typeof window !== "undefined") window.location.replace(path);
  };

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    const handleCallback = async () => {
      try {
        // ── Scenario 2: Backend sent access_token directly ──────────────────
        if (accessToken) {
          setStatus("Verifying your credentials…");

          // Let the backend validate the token and set HttpOnly session cookies
          const res = await fetch("/api/auth/restore", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              access_token: accessToken,
              refresh_token: refreshToken,
              redirect_to: redirectTo,
            }),
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
          }

          setStatus("Sign-in successful! Redirecting…");
          safeReplace(redirectTo);
          return;
        }

        // ── Scenario 3: Backend sent code + state (SSO Enterprise) ──────────
        if (code && state) {
          setStatus("Completing OAuth handshake…");

          const callbackPath = composeEndpoint("/auth/sso/callback", true);
          const res = await fetch(
            `${callbackPath}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
            { headers: { Accept: "application/json" }, credentials: "include" }
          );

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const msg = err.detail || `HTTP ${res.status}`;

            if (res.status === 410 || /invalid or expired state/i.test(msg)) {
              setStatus("Session expired. Redirecting to login…");
              setTimeout(() => safeReplace("/login"), 1500);
              return;
            }
            throw new Error(msg);
          }

          const data = await res.json();
          if (data.token?.access_token) {
            const restoreRes = await fetch("/api/auth/restore", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({
                access_token: data.token.access_token,
                refresh_token: data.token.refresh_token,
                redirect_to: data.redirect_to || redirectTo,
              }),
            });

            if (!restoreRes.ok) {
              throw new Error("Failed to restore session from SSO tokens");
            }

            setStatus("Sign-in successful! Redirecting…");
            safeReplace(data.redirect_to || redirectTo);
            return;
          }

          throw new Error(data.detail || "Authentication failed");
        }

        // ── No tokens, no code — nothing to do ──────────────────────────────
        setStatus("No session found. Redirecting to login…");
        setTimeout(() => safeReplace("/login"), 1500);
      } catch (err) {
        console.error("[AuthCallback]", err);
        setStatus(`Error: ${err instanceof Error ? err.message : "Authentication failed"}`);
        setTimeout(() => safeReplace("/login"), 3000);
      }
    };

    handleCallback();
  }, [accessToken, refreshToken, redirectTo, code, state]);

  return (
    <div className="w-full max-w-md rounded-2xl bg-white/5 p-8 text-center shadow-2xl backdrop-blur border border-white/10">
      <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-5" />
      <p className="text-sm text-slate-300 leading-relaxed">{status}</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8 bg-slate-950 relative overflow-hidden">
      {/* Ambient background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-fuchsia-500/5 rounded-full blur-[100px]" />
      </div>
      <div className="z-10 relative w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-white tracking-tight">GraftAI</h1>
          <p className="text-xs text-slate-500 mt-1">Securing your session…</p>
        </div>
        <Suspense
          fallback={
            <div className="w-full max-w-md rounded-2xl bg-white/5 p-8 text-center shadow-2xl backdrop-blur border border-white/10">
              <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-5" />
              <p className="text-sm text-slate-400">Preparing secure connection…</p>
            </div>
          }
        >
          <AuthCallbackInner />
        </Suspense>
      </div>
    </main>
  );
}
