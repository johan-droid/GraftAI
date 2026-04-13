import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

type BackendProfile = {
  preferences?: Record<string, unknown>;
};

export async function GET() {
  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;

  if (!backendToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_API_URL}/users/me`, {
      headers: {
        Authorization: `Bearer ${backendToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
  } catch (error) {
    console.error("Failed to fetch user preferences", error);
    return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
  }

  if (!backendRes.ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: backendRes.status });
  }

  const data = (await backendRes.json()) as BackendProfile;
  const preferences = data.preferences && typeof data.preferences === "object" ? data.preferences : {};

  return NextResponse.json({
    preferences,
    consents: {
      analytics: Boolean((preferences as Record<string, unknown>).consent_analytics ?? true),
      notifications: Boolean((preferences as Record<string, unknown>).consent_notifications ?? true),
      ai_training: Boolean((preferences as Record<string, unknown>).consent_ai_training ?? false),
    },
  });
}
