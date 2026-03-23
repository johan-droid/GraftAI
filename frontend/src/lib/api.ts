const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

import { clearToken, getToken, isTokenExpired } from "@/lib/auth";

interface ApiOptions {
  method?: string;
  body?: Record<string, unknown> | null;
  token?: string;
}

async function resolveUnauthorized() {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function apiFetch<T = unknown>(path: string, options: ApiOptions = {}) {
  const { method = "GET", body, token } = options;
  const tokenToUse = token || getToken();

  if (tokenToUse && isTokenExpired(tokenToUse)) {
    await resolveUnauthorized();
    throw new Error("Session expired");
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (tokenToUse) {
    headers["Authorization"] = `Bearer ${tokenToUse}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
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

// ──────────────────────────────────────
// Auth: Session Check
// Backend: GET /auth/check (Bearer token in header)
// ──────────────────────────────────────
export async function verifyToken(token: string) {
  return apiFetch<{ authenticated: boolean; user: Record<string, unknown> }>("/auth/check", {
    method: "GET",
    token,
  });
}

export async function doitAuthCheck() {
  return apiFetch<{ authenticated: boolean; user: Record<string, unknown> }>("/auth/check", {
    method: "GET",
  });
}

export async function refreshSession() {
  const token = getToken();
  if (!token) {
    throw new Error("No token to refresh");
  }
  if (isTokenExpired(token)) {
    throw new Error("Token expired");
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
export async function mfaSetup(userId: number) {
  return apiFetch("/auth/mfa/setup?" + new URLSearchParams({ user_id: String(userId) }), {
    method: "POST",
  });
}

export async function mfaVerify(userId: number, token: string) {
  return apiFetch<{ status: string }>(
    "/auth/mfa/verify?" + new URLSearchParams({ user_id: String(userId), token }),
    { method: "POST" }
  );
}

// ──────────────────────────────────────
// Auth: FIDO2 / WebAuthn
// Backend: GET  /auth/fido2/register?user_id=...
// Backend: POST /auth/fido2/register  (Pydantic body: {user_id, attestation})
// Backend: POST /auth/fido2/verify    (Pydantic body: {user_id, assertion})
// ──────────────────────────────────────
export async function fido2StartRegistration(userId: number) {
  return apiFetch("/auth/fido2/register?" + new URLSearchParams({ user_id: String(userId) }));
}

export async function fido2CompleteRegistration(userId: number, attestation: Record<string, unknown>) {
  return apiFetch<{ status: string }>("/auth/fido2/register", {
    method: "POST",
    body: { user_id: userId, attestation },
  });
}

export async function fido2Verify(userId: number, assertion: Record<string, unknown>) {
  return apiFetch<{ status: string }>("/auth/fido2/verify", {
    method: "POST",
    body: { user_id: userId, assertion },
  });
}

// ──────────────────────────────────────
// Auth: DID (Decentralized Identity)
// Backend: POST /auth/did/issue?user_id=...  (query param)
// Backend: POST /auth/did/verify  (Pydantic body: {user_id, did})
// ──────────────────────────────────────
export async function didIssue(userId: number) {
  return apiFetch<{ did: string }>(
    "/auth/did/issue?" + new URLSearchParams({ user_id: String(userId) }),
    { method: "POST" }
  );
}

export async function didVerify(userId: number, did: string) {
  return apiFetch<{ status: string }>("/auth/did/verify", {
    method: "POST",
    body: { user_id: userId, did },
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
export async function checkRole(userId: number, role: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-role?" + new URLSearchParams({ user_id: String(userId), role })
  );
}

export async function checkAttribute(userId: number, attribute: string, value: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-attribute?" + new URLSearchParams({ user_id: String(userId), attribute, value })
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
    body: { user_id: 1, context },
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
    body: { user_id: 1, consent_type: consentType, granted },
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
