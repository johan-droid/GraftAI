import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete({ name: "auth_token", path: "/" });
  response.cookies.delete({ name: "refresh_token", path: "/" });
  response.cookies.delete({ name: "graftai_access_token", path: "/" });
  response.cookies.delete({ name: "graftai_refresh_token", path: "/" });
  return response;
}
