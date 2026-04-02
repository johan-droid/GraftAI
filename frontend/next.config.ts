import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: "standalone",
  outputFileTracingRoot: path.resolve(__dirname, ".."),
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const backendBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/api/:path*`,
      },
      {
        source: "/auth/:path*",
        destination: `${backendBaseUrl}/auth/:path*`,
      },
      {
        source: "/health",
        destination: `${backendBaseUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
