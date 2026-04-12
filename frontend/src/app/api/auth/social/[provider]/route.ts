import { NextResponse } from "next/server";
import { BACKEND_API_URL } from "@/lib/backend";

const ALLOWED_PROVIDERS = new Set(["google", "microsoft", "microsoft-entra-id"]);

export async function GET(
  request: Request,
  { params }: { params: Promise<{ provider: string }> }
) {
  const { provider: rawProvider } = await params;
  const provider = rawProvider.toLowerCase();
  if (!ALLOWED_PROVIDERS.has(provider)) {
    return NextResponse.json({ error: "Unsupported provider" }, { status: 400 });
  }

  const url = new URL(request.url);
  const redirect_to = url.searchParams.get("redirect_to") || "/dashboard";
  const referer = request.headers.get("referer");
  const frontendUrl = referer ? new URL(referer).origin : url.origin;

  // Map internal frontend provider names to backend provider names
  const backendProvider = provider === "microsoft-entra-id" ? "microsoft" : provider;

  const authUrl = `${BACKEND_API_URL}/auth/${backendProvider}/login?redirect_to=${encodeURIComponent(
    redirect_to
  )}&frontend_url=${encodeURIComponent(frontendUrl)}`;

  return NextResponse.redirect(authUrl, 303);
}
