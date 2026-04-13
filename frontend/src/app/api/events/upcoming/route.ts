import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json([], { status: 401 });
  }

  const now = new Date().toISOString();
  const until = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(
      `${BACKEND_API_URL}/calendar/events?start=${encodeURIComponent(now)}&end=${encodeURIComponent(until)}`,
      {
        headers: { "Authorization": `Bearer ${backendToken}` },
        signal: controller.signal,
      }
    );
    clearTimeout(timeoutId);

    return res.ok
      ? NextResponse.json(await res.json())
      : NextResponse.json([], { status: res.status });
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      return NextResponse.json({ error: "Gateway Timeout" }, { status: 504 });
    }
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
