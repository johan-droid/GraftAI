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
    const errorPayload = await backendRes.json().catch(() => ({}));
    return NextResponse.json(
      { error: errorPayload.detail || "Unable to verify access token" },
      { status: 401 }
    );
  }

  const data = await backendRes.json();
  const response = NextResponse.json({
    ok: true,
    user: data.user || data,
    redirect_to,
    access_token,
    refresh_token,
  });

  response.cookies.set("auth_token", access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_TOKEN_MAX_AGE,
  });

  if (refresh_token) {
    response.cookies.set("refresh_token", refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: REFRESH_TOKEN_MAX_AGE,
    });
  }

  return response;
}
