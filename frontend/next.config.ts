import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  output: "standalone",
  // We don't want telemetry in production
  typescript: {
    ignoreBuildErrors: true, 
  },
};

export default nextConfig;
