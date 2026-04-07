import path from "path";
import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/sw.ts",
  swDest: "public/sw.js",
  reloadOnOnline: true,
  disable: process.env.NODE_ENV === "development",
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
    const backendBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
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
          destination: `${backendBaseUrl}/auth/:path*`,
        },
        {
          source: "/health",
          destination: `${backendBaseUrl}/health`,
        },
      ],
      // Keep generic /api proxy as fallback so local backend APIs are proxied.
      fallback: [
        {
          source: "/api/:path*",
          destination: `${backendBaseUrl}/api/:path*`,
        },
      ],
    };
  },
};

export default withSerwist(nextConfig);
