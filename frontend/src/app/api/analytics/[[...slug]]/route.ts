import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

// Redis caching — Upstash compatible
let redis: { get: (k: string) => Promise<string | null>; setex: (k: string, ttl: number, v: string) => Promise<any> } | null = null;

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

async function getAnalytics(accessToken: string) {
  const cacheKey = `analytics:${accessToken}`;
  const r = await getRedis();
  
  try {
    if (r) {
      const cached = await r.get(cacheKey);
      if (cached) return NextResponse.json(typeof cached === "string" ? JSON.parse(cached) : cached);
    }
  } catch (err) {
    console.error("Redis cache read failed:", err);
  }

  const res = await fetch(`${BACKEND_API_URL}/analytics/summary?range=7d`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${accessToken}`,
    },
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
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return getAnalytics(backendToken);
}

export async function POST(request: Request) {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return getAnalytics(backendToken);
}
