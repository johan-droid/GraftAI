import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: "standalone",
  outputFileTracingRoot: path.resolve(__dirname, ".."),
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
