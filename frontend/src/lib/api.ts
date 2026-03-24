const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

if (typeof window !== "undefined") {
  console.debug("API_BASE_URL set to", API_BASE_URL);
  if (
    process.env.NODE_ENV === "production" &&
    (API_BASE_URL.startsWith("http://localhost") || API_BASE_URL.startsWith("http://127.0.0.1"))
  ) {
    console.warn(
      "Running in production with localhost backend URL. Please set NEXT_PUBLIC_API_BASE_URL or NEXT_PUBLIC_BACKEND_URL to your deployed backend domain."
    );
  }
}

import { clearToken, getToken } from "@/lib/auth";

interface ApiOptions {
  method?: string;
  body?: Record<string, unknown> | null;
}

async function resolveUnauthorized() {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function apiFetch<T = unknown>(path: string, options: ApiOptions = {}) {
  const { method = "GET", body } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include", // Ensure HttpOnly cookies are sent
  });

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      await resolveUnauthorized();
      throw new Error("Unauthorized");
    }

    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ──────────────────────────────────────
// Auth: Credential Login
// Backend: POST /auth/token (OAuth2PasswordRequestForm → form-urlencoded)
// ──────────────────────────────────────
export async function login(username: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Login failed");
  }

  return res.json() as Promise<{ access_token: string; token_type: string }>;
}

export async function register(email: string, password: string, fullName?: string, timezone?: string) {
  return apiFetch<{ message: string; id: number }>("/auth/register", {
    method: "POST",
    body: { email, password, full_name: fullName, timezone },
  });
}

// ──────────────────────────────────────
// Auth: Session Check
// Backend: GET /auth/check (Bearer token in header)
// ──────────────────────────────────────
export async function verifyToken() {
  return apiFetch<{ authenticated: boolean; user: Record<string, unknown> }>("/auth/check", {
    method: "GET",
  });
}

export async function doitAuthCheck() {
  return apiFetch<{ authenticated: boolean; user: Record<string, unknown> }>("/auth/check", {
    method: "GET",
  });
}

export async function refreshSession() {
  const isLoggedIn = getToken();
  if (!isLoggedIn) {
    throw new Error("No session to refresh");
  }
  return doitAuthCheck();
}

// ──────────────────────────────────────
// Auth: Passwordless Magic Link
// Backend: POST /auth/passwordless/request?email=...  (query param)
// Backend: POST /auth/passwordless/verify?email=...&code=...  (query params)
// ──────────────────────────────────────
export async function passwordlessRequest(email: string) {
  return apiFetch("/auth/passwordless/request?" + new URLSearchParams({ email }), {
    method: "POST",
  });
}

export async function passwordlessVerify(email: string, code: string) {
  return apiFetch<{ access_token: string; token_type: string }>(
    "/auth/passwordless/verify?" + new URLSearchParams({ email, code }),
    { method: "POST" }
  );
}

// ──────────────────────────────────────
// Auth: MFA
// Backend: POST /auth/mfa/setup?user_id=...  (query param)
// Backend: POST /auth/mfa/verify?user_id=...&token=...  (query params)
// ──────────────────────────────────────
export async function mfaSetup() {
  return apiFetch("/auth/mfa/setup", {
    method: "POST",
  });
}

export async function mfaVerify(token: string) {
  return apiFetch<{ status: string }>(
    "/auth/mfa/verify?" + new URLSearchParams({ token }),
    { method: "POST" }
  );
}

// ──────────────────────────────────────
// Auth: FIDO2 / WebAuthn
// Backend: GET  /auth/fido2/register?user_id=...
// Backend: POST /auth/fido2/register  (Pydantic body: {user_id, attestation})
// Backend: POST /auth/fido2/verify    (Pydantic body: {user_id, assertion})
// ──────────────────────────────────────
export async function fido2StartRegistration() {
  return apiFetch("/auth/fido2/register");
}

export async function fido2CompleteRegistration(attestation: Record<string, unknown>) {
  return apiFetch<{ status: string }>("/auth/fido2/register", {
    method: "POST",
    body: { attestation },
  });
}

export async function fido2Verify(assertion: Record<string, unknown>) {
  return apiFetch<{ status: string }>("/auth/fido2/verify", {
    method: "POST",
    body: { assertion },
  });
}

// ──────────────────────────────────────
// Auth: DID (Decentralized Identity)
// Backend: POST /auth/did/issue?user_id=...  (query param)
// Backend: POST /auth/did/verify  (Pydantic body: {user_id, did})
// ──────────────────────────────────────
export async function didIssue() {
  return apiFetch<{ did: string }>(
    "/auth/did/issue",
    { method: "POST" }
  );
}

export async function didVerify(did: string) {
  return apiFetch<{ status: string }>("/auth/did/verify", {
    method: "POST",
    body: { did },
  }
  );
}

// ──────────────────────────────────────
// Auth: SSO Start
// Backend: GET /auth/sso/start?provider=...&redirect_to=...
// ──────────────────────────────────────
export async function ssoStart(provider: string = "github", redirectTo: string = "/dashboard") {
  return apiFetch<{ authorization_url: string; state: string }>(
    `/auth/sso/start?provider=${provider}&redirect_to=${encodeURIComponent(redirectTo)}`
  );
}

// ──────────────────────────────────────
// Auth: Access Control
// Backend: GET /auth/access-control/check-role?user_id=...&role=...
// Backend: GET /auth/access-control/check-attribute?user_id=...&attribute=...&value=...
// ──────────────────────────────────────
export async function checkRole(role: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-role?" + new URLSearchParams({ role })
  );
}

export async function checkAttribute(attribute: string, value: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-attribute?" + new URLSearchParams({ attribute, value })
  );
}

// ──────────────────────────────────────
// Services: Analytics
// Backend: POST /analytics/summary  (Pydantic body)
// ──────────────────────────────────────
export async function getAnalyticsSummary() {
  return apiFetch<{ summary: string; details?: { meetings: number; hours: number; growth: number } }>("/analytics/summary", {
    method: "POST",
    body: { range: "7d" },
  });
}

// ──────────────────────────────────────
// Services: AI Chat
// Backend: POST /ai/chat  (Pydantic body)
// ──────────────────────────────────────
export async function sendAiChat(prompt: string, context?: string[]) {
  return apiFetch<{ result: string; model_used?: string }>("/ai/chat", {
    method: "POST",
    body: { prompt, context },
  });
}

// ──────────────────────────────────────
// Services: Proactive Suggestions
// Backend: POST /proactive/suggest  (Pydantic body)
// ──────────────────────────────────────
export async function getProactiveSuggestion(context?: string) {
  return apiFetch<{ suggestion: string }>("/proactive/suggest", {
    method: "POST",
    body: { context },
  });
}

// ──────────────────────────────────────
// Services: Plugins
// Backend: GET /plugins/list
// ──────────────────────────────────────
export async function listPlugins() {
  return apiFetch<{ plugins: { name: string; description: string; version: string; author?: string }[] }>("/plugins/list");
}

// ──────────────────────────────────────
// Services: Consent
// Backend: POST /consent/set  (Pydantic body)
// ──────────────────────────────────────
export async function setConsent(consentType: string, granted: boolean) {
  return apiFetch<{ status: string }>("/consent/set", {
    method: "POST",
    body: { consent_type: consentType, granted },
  });
}

// ──────────────────────────────────────
// Services: LLM Upgrade
// Backend: POST /upgrade/llm  (Pydantic body)
// ──────────────────────────────────────
export async function upgradeLLM(modelName: string, version?: string) {
  return apiFetch<{ status: string; details?: string }>("/upgrade/llm", {
    method: "POST",
    body: { model_name: modelName, version },
  });
}
