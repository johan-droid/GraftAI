import { NextResponse } from "next/server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";
import {
  applyServerAuthCookies,
  resolveServerAccessToken,
} from "@/lib/server-auth";

export async function GET() {
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) {
    return NextResponse.json({ plugins: [] }, { status: 401 });
  }

  const res = await fetch(`${BACKEND_API_URL}/plugins/list`, {
    headers: { "Authorization": `Bearer ${tokenResolution.accessToken}` },
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ plugins: [] }, { status: res.status });
  }

  const response = NextResponse.json(await res.json());
  if (tokenResolution.refreshed) {
    applyServerAuthCookies(
      response,
      tokenResolution.accessToken,
      tokenResolution.refreshToken
    );
  }
  return response;
}
