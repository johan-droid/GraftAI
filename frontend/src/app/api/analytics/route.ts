import { NextResponse } from "next/server";
import { auth } from "@/lib/auth-server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";

// Redis caching — Upstash compatible
let redis: { get: (k: string) => Promise<string | null>; setex: (k: string, ttl: number, v: string) => Promise<void> } | null = null;

async function getRedis() {
  if (redis) return redis;
  if (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN) {
    const { Redis } = await import("@upstash/redis");
    redis = new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL,
      token: process.env.UPSTASH_REDIS_REST_TOKEN,
    });
  }
  return redis;
}

async function getAnalytics(session: any) {
  const cacheKey = `analytics:${session.user?.id || session.session?.token || "user"}`;
  const r = await getRedis();
  
  try {
    if (r) {
      const cached = await r.get(cacheKey);
      if (cached) return NextResponse.json(typeof cached === "string" ? JSON.parse(cached) : cached);
    }
  } catch (err) {
    console.error("Redis cache read failed:", err);
  }

  const res = await fetch(`${BACKEND_API_URL}/analytics/summary`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session.session.token}`,
    },
    body: JSON.stringify({ range: "7d" }),
  });

  if (!res.ok) return NextResponse.json({ error: "Backend error" }, { status: res.status });
  const data = await res.json();

  if (r) {
    try {
      await r.setex(cacheKey, 60, JSON.stringify(data));
    } catch (err) {
      console.error("Redis cache write failed:", err);
    }
  }

  return NextResponse.json(data);
}

export async function GET() {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return getAnalytics(session);
}

export async function POST(request: Request) {
  const reqHeaders = await headers();
  const session = await auth.api.getSession({ headers: reqHeaders });
  if (!session) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return getAnalytics(session);
}
