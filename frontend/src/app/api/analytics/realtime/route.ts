import { NextResponse } from "next/server";
import { createHash } from "crypto";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

// Lightweight Redis cache wrapper (Upstash compatible)
let redis: { get: (k: string) => Promise<string | null>; setex: (k: string, ttl: number, v: string) => Promise<any> } | null = null;
async function getRedis() {
  if (redis) return redis;
  if (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN) {
    const { Redis } = await import("@upstash/redis");
    redis = new Redis({ url: process.env.UPSTASH_REDIS_REST_URL, token: process.env.UPSTASH_REDIS_REST_TOKEN });
  }
  return redis;
}

async function proxyRealtime(accessToken: string, range: string) {
  const tokenHash = createHash("sha256").update(accessToken).digest("hex");
  const cacheKey = `analytics:realtime:${tokenHash}:${range}`;
  const r = await getRedis();
  try {
    if (r) {
      const cached = await r.get(cacheKey);
      if (cached) return NextResponse.json(typeof cached === "string" ? JSON.parse(cached) : cached);
    }
  } catch (err) {
    console.error("Redis cache read failed:", err);
  }

  const res = await fetch(`${BACKEND_API_URL}/analytics/realtime?range=${encodeURIComponent(range)}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) return NextResponse.json({ error: "Backend error" }, { status: res.status });
  const data = await res.json();

  if (r) {
    try {
      await r.setex(cacheKey, 30, JSON.stringify(data));
    } catch (err) {
      console.error("Redis cache write failed:", err);
    }
  }

  return NextResponse.json(data);
}

export async function GET(request: Request) {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;
  if (!backendToken) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const url = new URL(request.url);
  const range = url.searchParams.get("range") || "30d";
  return proxyRealtime(backendToken, range);
}

