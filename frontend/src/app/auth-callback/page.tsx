"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { composeEndpoint } from "@/lib/api-client";
import { Box, Typography } from "@mui/material";

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
import { AuthLayout } from "@/components/auth/AuthLayout";

/**
 * /auth-callback
 * 
 * Secure terminal for resolving the authentication handshake.
 * Supports NextAuth exchange (primary), Direct SSO redirects, and Enterprise Code flows.
 */
function AuthCallbackInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("RESOLVING_AUTH_HANDSHAKE...");
  const [telemetry, setTelemetry] = useState<string[]>([]);
  const hasFetched = useRef(false);

  const accessToken  = searchParams.get("at") || searchParams.get("access_token");
  const refreshToken = searchParams.get("rt") || searchParams.get("refresh_token");
  const redirectTo   = searchParams.get("redirect") || "/dashboard";
  const code         = searchParams.get("code");
  const state        = searchParams.get("state");

  const addTelemetry = (msg: string) => {
    setTelemetry(prev => [...prev.slice(-3), `> ${msg}`]);
  };

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
          safeReplace(redirectTo);
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
            safeReplace(data.redirect_to || redirectTo);
            return;
          }

          throw new Error(data.detail || "AUTH_NODE_FAULT");
        }

        // ── Scenario 1: NextAuth handles directly — should barely blink if we end up here
        setStatus("POLLING_SESSION_INTEGRITY...");
        setTimeout(() => safeReplace("/dashboard"), 1000);

      } catch (err) {
        console.error("[AuthCallback]", err);
        setStatus(`ERROR_CODE: ${err instanceof Error ? err.message : "AUTH_GENERAL_FAULT"}`);
        addTelemetry("CRITICAL_NODE_FAILURE");
        setTimeout(() => safeReplace("/login"), 3000);
      }
    };

    handleCallback();
  }, [accessToken, refreshToken, redirectTo, code, state]);

  return (
    <Box sx={{ width: "100%" }}>
      <Box 
        sx={{ 
          display: "flex", 
          flexDirection: "column", 
          alignItems: "center", 
          gap: 4,
          py: 4 
        }}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            border: "2px solid var(--border-subtle)",
            borderTopColor: "var(--primary)",
            borderRadius: 0,
            animation: "spin 1s linear infinite",
          }}
        />
        
        <Box sx={{ textAlign: "center", width: "100%" }}>
          <Typography
            sx={{
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              fontWeight: 900,
              color: "var(--primary)",
              letterSpacing: "0.1em",
              mb: 2,
              textTransform: "uppercase",
            }}
          >
            {status}
          </Typography>
          
          <Box 
            sx={{ 
              mt: 4, 
              p: 2, 
              background: "rgba(0,0,0,0.3)", 
              border: "1px dashed var(--border-subtle)",
              textAlign: "left",
              minHeight: "100px"
            }}
          >
            {telemetry.map((line, i) => (
              <Typography 
                key={i} 
                sx={{ 
                  fontFamily: "var(--font-mono)", 
                  fontSize: "10px", 
                  color: "var(--text-faint)",
                  mb: 0.5 
                }}
              >
                {line}
              </Typography>
            ))}
            <Box sx={{ 
              width: "8px", 
              height: "2px", 
              background: "var(--primary)", 
              display: "inline-block",
              animation: "pulse 1s infinite",
              verticalAlign: "middle",
              ml: 1
            }} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default function AuthCallback() {
  return (
    <AuthLayout 
      title="SESSION_RESOLVER" 
      subtitle="GRAFT_AI :: THREAT_ASSESSMENT_&_IDENTITY_ANCHOR"
    >
      <Suspense
        fallback={
          <Box 
            sx={{ 
              display: "flex", 
              flexDirection: "column", 
              alignItems: "center", 
              gap: 4,
              py: 8
            }}
          >
            <Box
              sx={{
                width: 40,
                height: 40,
                border: "2px solid var(--border-subtle)",
                borderTopColor: "var(--primary)",
                borderRadius: 0,
                animation: "spin 1.5s linear infinite",
              }}
            />
            <Typography sx={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)" }}>
              INITIALIZING_ANCHOR...
            </Typography>
          </Box>
        }
      >
        <AuthCallbackInner />
      </Suspense>
    </AuthLayout>
  );
}

