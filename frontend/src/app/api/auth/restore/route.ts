import { NextResponse } from "next/server";
import { BACKEND_API_URL } from "@/lib/backend";

const ACCESS_TOKEN_MAX_AGE = 15 * 60;
const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60;

export async function POST(request: Request) {
  let body;
  try {
    body = await request.json();
  } catch (error) {
    console.error("Restore request parse error", error);
    return NextResponse.json({ error: "Invalid JSON in request body" }, { status: 400 });
  }

  const access_token = body.access_token?.toString();
  const refresh_token = body.refresh_token?.toString();
  const redirect_to = body.redirect_to?.toString() || "/dashboard";

  if (!access_token) {
    return NextResponse.json({ error: "Missing access token" }, { status: 400 });
  }

  const backendRes = await fetch(`${BACKEND_API_URL}/auth/check`, {
    headers: {
      Authorization: `Bearer ${access_token}`,
      "Content-Type": "application/json",
    },
  });

  if (!backendRes.ok) {
    const errorPayload = await backendRes
      .text()
      .then((text) => {
        if (!text) return {};
        try {
          return JSON.parse(text);
        } catch {
          return {};
        }
      })
      .catch(() => ({}));

    return NextResponse.json(
      { error: (errorPayload as any).detail || "Unable to verify access token" },
      { status: 401 }
    );
  }

  const bodyText = await backendRes.text();
  let data: Record<string, unknown> = {};
  if (bodyText) {
    try {
      data = JSON.parse(bodyText) as Record<string, unknown>;
    } catch (error) {
      console.error("Restore response parse error", error, bodyText);
    }
  }

  const response = NextResponse.json({
    ok: true,
    user: data.user || data,
    redirect_to,
    access_token,
    refresh_token,
  });

  const cookieOptions = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: ACCESS_TOKEN_MAX_AGE,
  };

  // Standardizing on graftai_ prefix for consistency with backend logic
  response.cookies.set("auth_token", access_token, cookieOptions);
  response.cookies.set("graftai_access_token", access_token, cookieOptions);

  if (refresh_token) {
    const refreshCookieOptions = {
      ...cookieOptions,
      maxAge: REFRESH_TOKEN_MAX_AGE,
    };
    response.cookies.set("refresh_token", refresh_token, refreshCookieOptions);
    response.cookies.set("graftai_refresh_token", refresh_token, refreshCookieOptions);
  }

  return response;
}
