import path from "path";
import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/sw.ts",
  swDest: "public/sw.js",
  cacheOnNavigation: true,
  reloadOnOnline: true,
  disable:
    process.env.NODE_ENV === "development" ||
    process.env.NEXT_PUBLIC_DISABLE_SERVICE_WORKER === "true",
  exclude: [
    /\.map$/,
    /^manifest.*\.js(?:on)?$/,
    /\.js\.map$/,
    /^middleware-manifest\.json$/,
    /_next\/static\/chunks\/remoteEntry\.js$/,
    /_next\/static\/.*\/_ssgManifest\.js$/,
    /_next\/static\/.*\/_buildManifest\.js$/,
  ],
});

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: "standalone",
  outputFileTracingRoot: path.resolve(__dirname, ".."),
  typescript: {
    ignoreBuildErrors: true,
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [375, 640, 750, 828, 1080, 1200],
  },
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store, no-cache, must-revalidate, proxy-revalidate",
          },
          {
            key: "Content-Type",
            value: "application/javascript",
          },
          {
            key: "Service-Worker-Allowed",
            value: "/",
          },
        ],
      },
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          // Static CSP removed - migrating to dynamic nonce-based CSP in middleware.ts
        ],
      },
    ];
  },
  async rewrites() {
    const defaultBackend =
      process.env.NODE_ENV === "production"
        ? "https://graftai.onrender.com"
        : "http://127.0.0.1:8000";
    const rawBackendBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      defaultBackend;
    const normalizedBackendBaseUrl = rawBackendBaseUrl.replace(/\/+$/, "");
    const backendOrigin = normalizedBackendBaseUrl.endsWith("/api/v1")
      ? normalizedBackendBaseUrl.slice(0, -"/api/v1".length)
      : normalizedBackendBaseUrl;
    const backendApiBase = normalizedBackendBaseUrl.endsWith("/api/v1")
      ? normalizedBackendBaseUrl
      : `${backendOrigin}/api/v1`;

    return {
      beforeFiles: [
        {
          source: "/api/auth/:path*",
          destination: "/api/auth/:path*",
        },
      ],
      afterFiles: [
        {
          source: "/auth/:path*",
          destination: `${backendApiBase}/auth/:path*`,
        },
        {
          source: "/health",
          destination: `${backendOrigin}/health`,
        },
      ],
      // Keep generic /api proxy as fallback so local backend APIs are proxied.
      fallback: [
        {
          source: "/api/:path*",
          destination: `${backendApiBase}/:path*`,
        },
      ],
    };
  },
};

export default withSerwist(nextConfig);
