import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";

export async function GET() {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) return NextResponse.json([], { status: 401 });

  const now = new Date().toISOString();
  const until = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(
      `${BACKEND_API_URL}/calendar/events?start=${encodeURIComponent(now)}&end=${encodeURIComponent(until)}`,
      { 
        headers: { "Authorization": `Bearer ${session.session.token}` },
        signal: controller.signal 
      }
    );
    clearTimeout(timeoutId);

    if (!res.ok) return NextResponse.json([], { status: res.status });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      return NextResponse.json({ error: "Gateway Timeout" }, { status: 504 });
    }
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
