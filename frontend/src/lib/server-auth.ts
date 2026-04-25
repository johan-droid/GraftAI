import type { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { BACKEND_API_URL } from "@/lib/backend";

const ACCESS_TOKEN_MAX_AGE = 15 * 60;
const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60;

export type ServerTokenResolution = {
  accessToken: string | null;
  refreshToken?: string;
  refreshed: boolean;
};

export async function resolveServerAccessToken(reqHeaders: Headers): Promise<ServerTokenResolution> {
  const session = await auth.api.getSession({ headers: reqHeaders });
  const sessionToken = session?.session?.token;
  if (sessionToken) {
    return { accessToken: sessionToken, refreshed: false };
  }

  // 2. Check Authorization header
  const authHeader = reqHeaders.get("Authorization");
  if (authHeader?.startsWith("Bearer ")) {
    const token = authHeader.substring(7);
    return { accessToken: token, refreshed: false };
  }

  const cookieHeader = reqHeaders.get("cookie");
  if (!cookieHeader) {
    return { accessToken: null, refreshed: false };
  }

  // Look for existing access token in cookies
  // SECURITY FIX H-10: Only check primary cookie name (graftai_access_token)
  // Legacy auth_token is deprecated and should not be checked
  const match = cookieHeader.match(/graftai_access_token=([^;]+)/);
  if (match && match[1]) {
    const token = match[1];
    try {
      // SECURITY: Do not trust client-side JWT decoding without signature verification
      // Always validate token expiry through backend or use jose.jwtVerify with secret
      // For now, check with backend introspection endpoint or attempt refresh
      // Client-side expiry check is for UX optimization only - backend validates signature
      const payloadBase64 = token.split('.')[1];
      const payloadStr = Buffer.from(payloadBase64, 'base64').toString('utf8');
      const payload = JSON.parse(payloadStr);
      // Check if token is valid for at least another minute
      if (payload.exp && payload.exp * 1000 > Date.now() + 60000) {
        // Validate token with backend introspection endpoint
        const introspectionResponse = await fetch(`${BACKEND_API_URL}/auth/introspect`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `token=${token}`,
        });
        if (introspectionResponse.ok) {
          const introspectionData = await introspectionResponse.json();
          if (introspectionData.active) {
            return { accessToken: token, refreshed: false };
          }
        }
      }
    } catch (e) {
      // Token parsing failed, continue to refresh
    }
  }

  try {
    const refreshRes = await fetch(`${BACKEND_API_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        Cookie: cookieHeader,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!refreshRes.ok) {
      return { accessToken: null, refreshed: false };
    }

    const refreshData = (await refreshRes.json().catch(() => ({}))) as {
      access_token?: unknown;
      refresh_token?: unknown;
    };

    const accessToken =
      typeof refreshData.access_token === "string" ? refreshData.access_token : null;
    const refreshToken =
      typeof refreshData.refresh_token === "string" ? refreshData.refresh_token : undefined;

    return {
      accessToken,
      refreshToken,
      refreshed: Boolean(accessToken),
    };
  } catch (error) {
    console.error("Failed to refresh access token", error);
    return { accessToken: null, refreshed: false };
  }
}

export function applyServerAuthCookies(
  response: NextResponse,
  accessToken: string,
  refreshToken?: string
) {
  const cookieOptions = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: ACCESS_TOKEN_MAX_AGE,
  };

  // SECURITY FIX H-10: Standardize on single cookie to prevent auth confusion
  // Previously we had dual cookies which could lead to inconsistent state
  // Primary cookie name: graftai_access_token (explicit, branded)
  response.cookies.set("graftai_access_token", accessToken, cookieOptions);
  
  // Clear legacy auth_token to prevent stale/untampered cookie issues
  response.cookies.set("auth_token", "", { ...cookieOptions, maxAge: 0 });

  if (refreshToken) {
    const refreshCookieOptions = {
      ...cookieOptions,
      maxAge: REFRESH_TOKEN_MAX_AGE,
    };
    response.cookies.set("graftai_refresh_token", refreshToken, refreshCookieOptions);
    // Clear legacy refresh_token
    response.cookies.set("refresh_token", "", { ...refreshCookieOptions, maxAge: 0 });
  }
}
