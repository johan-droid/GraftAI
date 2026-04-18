"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { composeEndpoint } from "@/lib/api-client";
import { AppLoadingScreen } from "@/components/ui/AppLoadingScreen";

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
 *      #at=...&rt=...&redirect=... (or legacy query params)
 *    We call /api/auth/restore to validate and set HttpOnly cookies,
 *    then navigate to the target.
 *
 * 3. Backend code+state flow
 *    The backend sends ?code=...&state=... for SSO Enterprise flows.
 */
/**
 * /auth-callback
 * 
 * Secure terminal for resolving the authentication handshake.
 * Supports NextAuth exchange (primary), Direct SSO redirects, and Enterprise Code flows.
 */
function AuthCallbackInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("RESOLVING_AUTH_HANDSHAKE...");
  const [, setTelemetry] = useState<string[]>([]);
  const [fragmentParams, setFragmentParams] = useState<URLSearchParams | null>(null);
  const [fragmentReady, setFragmentReady] = useState(false);
  const hasFetched = useRef(false);

  const accessToken  = fragmentParams?.get("at") || fragmentParams?.get("access_token") || searchParams.get("at") || searchParams.get("access_token");
  const refreshToken = fragmentParams?.get("rt") || fragmentParams?.get("refresh_token") || searchParams.get("rt") || searchParams.get("refresh_token");
  const redirectTo   = fragmentParams?.get("redirect") || searchParams.get("redirect") || "/dashboard";
  const skipSetup    = searchParams.get("skip_setup") === "true" || redirectTo.includes("skip_setup");
  const code         = searchParams.get("code");
  const state        = searchParams.get("state");
  const isErrorState = status.startsWith("ERROR_CODE:");
  const screenTitle = isErrorState ? "Sign in failed" : "Completing sign in";
  const screenSubtitle = isErrorState
    ? "We could not restore your session. Redirecting you back to sign in."
    : "Restoring your session and opening the right workspace.";

  const addTelemetry = (msg: string) => {
    setTelemetry(prev => [...prev.slice(-3), `> ${msg}`]);
  };

  const safeReplace = (path: string) => {
    if (typeof window !== "undefined") window.location.replace(path);
  };

  useEffect(() => {
    if (typeof window === "undefined") {
      setFragmentReady(true);
      return;
    }

    const hash = window.location.hash.startsWith("#")
      ? window.location.hash.slice(1)
      : "";

    const params = new URLSearchParams(hash);
    setFragmentParams(params);
    setFragmentReady(true);

    if (params.get("at") || params.get("access_token") || params.get("rt") || params.get("refresh_token")) {
      window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
    }
  }, []);

  useEffect(() => {
    if (!fragmentReady) return;
    if (hasFetched.current) return;
    hasFetched.current = true;

    const handleCallback = async () => {
      try {
        // ── Scenario 2: Backend sent access_token directly ──────────────────
        if (accessToken) {
          setStatus("VALIDATING_SOCIAL_CREDENTIALS...");
          addTelemetry("PKCE_HANDSHAKE_COMPLETE");
          addTelemetry("INIT_SESSION_RESTORATION");

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

          addTelemetry("KERNEL_SESSION_MOUNTED_OK");
          setStatus("SEQUENCE_SUCCESSFUL. REDIRECTING...");
          
          // If skip_setup is set, ensure we go to dashboard directly
          const finalRedirect = skipSetup 
            ? "/dashboard" 
            : redirectTo;
          safeReplace(finalRedirect);
          return;
        }

        // ── Scenario 3: Backend sent code + state (SSO Enterprise) ──────────
        if (code && state) {
          setStatus("EXCHANGING_SSO_CODE...");
          addTelemetry("NEGOTIATING_UPSTREAM_PROVIDERS");

          const callbackPath = composeEndpoint("/auth/sso/callback", true);
          const res = await fetch(
            `${callbackPath}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}&fetch=true`,
            { headers: { Accept: "application/json" }, credentials: "include" }
          );

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const msg = err.detail || `HTTP ${res.status}`;

            if (res.status === 410 || /invalid or expired state/i.test(msg)) {
              setStatus("HANDSHAKE_EXPIRED. RE-INITIALIZING...");
              setTimeout(() => safeReplace("/login"), 1500);
              return;
            }
            throw new Error(msg);
          }

          const data = await res.json();
          if (data.token?.access_token) {
            addTelemetry("PROVIDER_TRUST_ESTABLISHED");
            setStatus("MOUNTING_PERSISTENT_SESSION...");

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
              throw new Error("RESTORATION_FAULT_DETECTED");
            }

            setStatus("ACCESS_GRANTED_BY_KERNEL.");
            
            // If skip_setup is set, ensure we go to dashboard directly
            const finalRedirect = skipSetup 
              ? "/dashboard" 
              : (data.redirect_to || redirectTo);
            safeReplace(finalRedirect);
            return;
          }

          throw new Error(data.detail || "AUTH_NODE_FAULT");
        }

        // ── Scenario 1: NextAuth handles directly — should barely blink if we end up here
        setStatus("POLLING_SESSION_INTEGRITY...");
        // Always redirect to dashboard, skip any profile setup
        setTimeout(() => safeReplace("/dashboard"), 1000);

      } catch (err) {
        console.error("[AuthCallback]", err);
        setStatus(`ERROR_CODE: ${err instanceof Error ? err.message : "AUTH_GENERAL_FAULT"}`);
        addTelemetry("CRITICAL_NODE_FAILURE");
        setTimeout(() => safeReplace("/login"), 3000);
      }
    };

    handleCallback();
  }, [accessToken, refreshToken, redirectTo, code, state, fragmentReady]);

  return (
    <AppLoadingScreen
      variant="auth"
      title={screenTitle}
      subtitle={screenSubtitle}
    />
  );
}

export default function AuthCallback() {
  return (
    <Suspense
      fallback={
        <AppLoadingScreen
          variant="auth"
          title="Completing sign in"
          subtitle="Restoring your session and opening the right workspace."
        />
      }
    >
      <AuthCallbackInner />
    </Suspense>
  );
}

