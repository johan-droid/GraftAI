import { NextResponse } from "next/server";
import { BACKEND_API_URL } from "@/lib/backend";

const ALLOWED_PROVIDERS = new Set(["google", "microsoft"]);

export async function GET(
  request: Request,
  paramsPromise: Promise<{ params: { provider: string } }>
) {
  const { params } = await paramsPromise;
  const provider = params.provider.toLowerCase();
  if (!ALLOWED_PROVIDERS.has(provider)) {
    return NextResponse.json({ error: "Unsupported provider" }, { status: 400 });
  }

  const url = new URL(request.url);
  const redirect_to = url.searchParams.get("redirect_to") || "/dashboard";
  const referer = request.headers.get("referer");
  const frontendUrl = referer ? new URL(referer).origin : url.origin;

  const authUrl = `${BACKEND_API_URL}/auth/${provider}/login?redirect_to=${encodeURIComponent(
    redirect_to
  )}&frontend_url=${encodeURIComponent(frontendUrl)}`;

  return NextResponse.redirect(authUrl, 303);
}
