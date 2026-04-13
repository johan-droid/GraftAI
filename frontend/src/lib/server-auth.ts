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
  const match = cookieHeader.match(/(?:graftai_access_token|auth_token)=([^;]+)/);
  if (match && match[1]) {
    const token = match[1];
    try {
      const payloadBase64 = token.split('.')[1];
      const payloadStr = Buffer.from(payloadBase64, 'base64').toString('utf8');
      const payload = JSON.parse(payloadStr);
      // Check if token is valid for at least another minute
      if (payload.exp && payload.exp * 1000 > Date.now() + 60000) {
        return { accessToken: token, refreshed: false };
      }
    } catch (e) {
      // Decode failed or invalid token, fall through to attempt refresh
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

  response.cookies.set("auth_token", accessToken, cookieOptions);
  response.cookies.set("graftai_access_token", accessToken, cookieOptions);

  if (refreshToken) {
    const refreshCookieOptions = {
      ...cookieOptions,
      maxAge: REFRESH_TOKEN_MAX_AGE,
    };
    response.cookies.set("refresh_token", refreshToken, refreshCookieOptions);
    response.cookies.set("graftai_refresh_token", refreshToken, refreshCookieOptions);
  }
}
