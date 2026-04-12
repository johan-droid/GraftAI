import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete("auth_token", { path: "/" });
  response.cookies.delete("refresh_token", { path: "/" });
  response.cookies.delete("graftai_access_token", { path: "/" });
  response.cookies.delete("graftai_refresh_token", { path: "/" });
  return response;
}
