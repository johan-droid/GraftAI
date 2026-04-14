// Resolve the backend base URL with server-only env vars taking priority.
//
// BACKEND_URL and INTERNAL_BACKEND_URL are intended for Node.js/server-side
// contexts only (API routes, server utilities, and NextAuth callbacks).
// - BACKEND_URL: public backend endpoint, preferred for standard backend calls.
// - INTERNAL_BACKEND_URL: internal/private backend endpoint used for service-to-
//   service, internal network, or non-browser traffic.
//
// Public NEXT_PUBLIC_* vars are browser-exposed URLs and should only be used
// when the value must be available in client-side code.
const defaultBackendBase =
  process.env.NODE_ENV === "production"
    ? "https://graftai.onrender.com"
    : "http://127.0.0.1:8000";

const rawBackendBase =
  process.env.BACKEND_URL ||
  process.env.INTERNAL_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  defaultBackendBase;

const normalizedBackendBase = rawBackendBase
  ? rawBackendBase.replace(/\/api\/v1$/, "").replace(/\/+$/, "")
  : "";

const backendBase = normalizedBackendBase
  ? normalizedBackendBase.endsWith("/api/v1")
    ? normalizedBackendBase.slice(0, -"/api/v1".length)
    : normalizedBackendBase
  : "";

export const BACKEND_BASE_URL = backendBase;
export const BACKEND_API_URL = normalizedBackendBase
  ? normalizedBackendBase.endsWith("/api/v1")
    ? normalizedBackendBase
    : `${normalizedBackendBase}/api/v1`
  : "/api/v1";
