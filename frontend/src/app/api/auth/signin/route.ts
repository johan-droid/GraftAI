import { NextResponse } from "next/server";
import { BACKEND_API_URL } from "@/lib/backend";

const ACCESS_TOKEN_MAX_AGE = 15 * 60;
const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60;

export async function POST(request: Request) {
  let body;
  try {
    body = await request.json();
  } catch (error) {
    console.error("Signin request parse error", error);
    return NextResponse.json({ error: "Invalid JSON in request body" }, { status: 400 });
  }

  const { email, password } = body;
  if (!email || !password) {
    return NextResponse.json({ error: "Email and password are required" }, { status: 400 });
  }

  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const loginRes = await fetch(`${BACKEND_API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  if (!loginRes.ok) {
    const errorPayload = await loginRes.json().catch(() => ({}));
    return NextResponse.json({ error: errorPayload.detail || "Login failed" }, { status: loginRes.status });
  }

  const loginData = await loginRes.json();
  const access_token = loginData.access_token;
  const refresh_token = loginData.refresh_token;

  const checkRes = await fetch(`${BACKEND_API_URL}/auth/check`, {
    headers: {
      Authorization: `Bearer ${access_token}`,
      "Content-Type": "application/json",
    },
  });

  if (!checkRes.ok) {
    const errorPayload = await checkRes.json().catch(() => ({}));
    return NextResponse.json({ error: errorPayload.detail || "Unable to verify user" }, { status: 401 });
  }

  const userData = await checkRes.json();
  const response = NextResponse.json({ user: userData.user || userData, access_token, refresh_token });

  const cookieOptions = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_TOKEN_MAX_AGE,
  };

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
