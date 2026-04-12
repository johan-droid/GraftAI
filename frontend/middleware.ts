import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  // 1. Generate Nonce
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");

  // 2. Define CSP Policy
  // Note: 'strict-dynamic' allows scripts loaded by trusted (nonced) scripts to execute.
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-eval';
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' blob: data: https:;
    font-src 'self' https://fonts.gstatic.com;
    object-src 'none';
    base-uri 'none';
    form-action 'self';
    frame-ancestors 'none';
    frame-src 'self' https://checkout.razorpay.com https://api.razorpay.com;
    connect-src 'self' 
      https://*.onrender.com 
      https://*.vercel.app 
      https://ipapi.co
      ${process.env.NEXT_PUBLIC_API_BASE_URL || ""} 
      ${process.env.NEXT_PUBLIC_BACKEND_URL || ""};
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, " ").trim();

  // 3. Set Request Headers (to pass nonce to Layout/Components)
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", cspHeader);

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  // 4. Set Response Headers
  response.headers.set("Content-Security-Policy", cspHeader);

  // 5. Existing Dashboard Auth Logic
  const isDashboardRoute = request.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboardRoute) {
    const accessToken =
      request.cookies.get("graftai_access_token")?.value ||
      request.cookies.get("auth_token")?.value;
    const refreshToken =
      request.cookies.get("graftai_refresh_token")?.value ||
      request.cookies.get("refresh_token")?.value;

    if (!accessToken && !refreshToken) {
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return response;
}

export const config = {
  matcher: ["/dashboard", "/dashboard/:path*", "/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
