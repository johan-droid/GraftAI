"use client";

import { useMemo, useState } from "react";

const STORAGE_KEY = "graftai_is_logged_in";

export function getToken() {
  if (typeof window === "undefined") return null;
  // We no longer return the raw JWT for security (XSS).
  // Return a flag so the UI knows to attempt authenticated requests.
  return localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  // Never store the actual token in localStorage.
  // We only set a flag so the UI knows we are 'authenticated' without seeing the secret.
  localStorage.setItem(STORAGE_KEY, "true");
}

export function clearToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
  // Backend will handle clearing the HttpOnly cookie via /auth/logout
}

// NOTE: decodeJwtPayload and isTokenExpired are removed because 
// HttpOnly cookies prevent the frontend from reading the JWT.
// Session expiry is now handled by the backend (401 response).

export function ensureTokenValid() {
  return Boolean(getToken());
}

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(getToken());

  const isAuthenticated = useMemo(() => Boolean(token), [token]);

  function login(token: string) {
    setToken(token);
    setTokenState(token);
  }

  function logout() {
    clearToken();
    setTokenState(null);
  }

  return { token, isAuthenticated, login, logout };
}
