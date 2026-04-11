const rawBackendBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const normalizedBackendBase = rawBackendBase.replace(/\/+$/, "");

const backendBase = normalizedBackendBase.endsWith("/api/v1")
  ? normalizedBackendBase.slice(0, -"/api/v1".length)
  : normalizedBackendBase;

export const BACKEND_BASE_URL = backendBase;
export const BACKEND_API_URL = normalizedBackendBase.endsWith("/api/v1")
  ? normalizedBackendBase
  : `${normalizedBackendBase}/api/v1`;
