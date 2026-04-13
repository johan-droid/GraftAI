import { NextResponse } from "next/server";
import { headers } from "next/headers";
import { BACKEND_API_URL } from "@/lib/backend";
import { applyServerAuthCookies, resolveServerAccessToken } from "@/lib/server-auth";

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
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const response = await getAnalytics(tokenResolution.accessToken);
  if (tokenResolution.refreshed) {
    applyServerAuthCookies(response, tokenResolution.accessToken, tokenResolution.refreshToken);
  }
  return response;
}

export async function POST(request: Request) {
  const reqHeaders = await headers();
  const tokenResolution = await resolveServerAccessToken(reqHeaders);
  if (!tokenResolution.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const response = await getAnalytics(tokenResolution.accessToken);
  if (tokenResolution.refreshed) {
    applyServerAuthCookies(response, tokenResolution.accessToken, tokenResolution.refreshToken);
  }
  return response;
}
