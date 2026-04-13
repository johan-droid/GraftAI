import { NextResponse } from "next/server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";
import { applyServerAuthCookies, resolveServerAccessToken } from "@/lib/server-auth";

export async function GET() {
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) return NextResponse.json([], { status: 401 });

  const now = new Date().toISOString();
  const until = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(
      `${BACKEND_API_URL}/calendar/events?start=${encodeURIComponent(now)}&end=${encodeURIComponent(until)}`,
      {
        headers: { "Authorization": `Bearer ${tokenResolution.accessToken}` },
        signal: controller.signal,
      }
    );
    clearTimeout(timeoutId);

    const response = res.ok
      ? NextResponse.json(await res.json())
      : NextResponse.json([], { status: res.status });

    if (tokenResolution.refreshed) {
      applyServerAuthCookies(response, tokenResolution.accessToken, tokenResolution.refreshToken);
    }

    return response;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      return NextResponse.json({ error: "Gateway Timeout" }, { status: 504 });
    }
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
