"use client";

import { useMemo, useState } from "react";

const STORAGE_KEY = "graftai_access_token";

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, token);
  document.cookie = `graftai_access_token=${token}; path=/; max-age=${60 * 60 * 24};`; // 1 day
}

export function clearToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
  document.cookie = "graftai_access_token=; path=/; max-age=0";
}

export function decodeJwtPayload(token: string) {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decodeURIComponent(Array.prototype.map.call(decoded, (c: string) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)).join("")));
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string) {
  const payload = decodeJwtPayload(token);
  if (!payload || !payload.exp) return true;
  const expiresAt = payload.exp * 1000;
  return Date.now() > expiresAt;
}

export function ensureTokenValid() {
  const token = getToken();
  if (!token) return false;
  if (isTokenExpired(token)) {
    clearToken();
    return false;
  }
  return true;
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
