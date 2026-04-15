import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { BACKEND_API_URL } from "@/lib/backend";

const ALLOWED_PROVIDERS = new Set(["google", "microsoft", "microsoft-entra-id"]);

function sanitizeRedirectPath(value: string | null): string {
  if (!value) return "/dashboard";
  if (value.startsWith("http://") || value.startsWith("https://") || value.startsWith("//")) {
    return "/dashboard";
  }
  return value.startsWith("/") ? value : `/${value}`;
}

function resolveFrontendOrigin(url: URL): string {
  const configured =
    process.env.NEXT_PUBLIC_APP_URL ||
    process.env.FRONTEND_URL ||
    process.env.FRONTEND_BASE_URL;

  if (configured) {
    const first = configured.split(",")[0]?.trim();
    if (first) {
      try {
        return new URL(first).origin;
      } catch {
        // Fall back to request origin when env value is malformed.
      }
    }
  }

  return url.origin;
}

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
  const redirect_to = sanitizeRedirectPath(url.searchParams.get("redirect_to"));
  const frontendUrl = resolveFrontendOrigin(url);

  // Map internal frontend provider names to backend provider names
  const backendProvider = provider === "microsoft-entra-id" ? "microsoft" : provider;

  const backendLoginUrl = new URL(`${BACKEND_API_URL}/auth/${backendProvider}/login`);
  backendLoginUrl.searchParams.set("redirect_to", redirect_to);
  backendLoginUrl.searchParams.set("frontend_url", frontendUrl);

  const session = await auth();
  const backendToken = (session as any)?.backendToken || (session as any)?.session?.backendToken;

  const upstreamHeaders: HeadersInit = backendToken
    ? { Authorization: `Bearer ${backendToken}` }
    : {};

  const upstream = await fetch(backendLoginUrl.toString(), {
    method: "GET",
    headers: upstreamHeaders,
    redirect: "manual",
    cache: "no-store",
  });

  const locationHeader = upstream.headers.get("location");
  if (upstream.status >= 300 && upstream.status < 400 && locationHeader) {
    return NextResponse.redirect(locationHeader, 303);
  }

  const detail = await upstream.text().catch(() => "OAuth initiation failed");
  return NextResponse.json(
    { error: "OAuth initiation failed", detail: detail.slice(0, 500) },
    { status: upstream.status || 502 }
  );
}
