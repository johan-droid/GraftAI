const rawBackendBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "";

const normalizedBackendBase = rawBackendBase ? rawBackendBase.replace(/\/+$/, "") : "";

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
