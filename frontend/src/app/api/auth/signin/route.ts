import { NextResponse } from "next/server";

const BACKEND =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

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

  const loginRes = await fetch(`${BACKEND}/api/v1/auth/login`, {
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

  const checkRes = await fetch(`${BACKEND}/api/v1/auth/check`, {
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
