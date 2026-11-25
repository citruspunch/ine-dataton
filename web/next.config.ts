import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The route handler and the server-rendered page read the generated JSON
  // bundle from web/data. Include it in the traced output for `next start`.
  outputFileTracingIncludes: {
    "/*": ["./data/**/*"],
    "/api/records": ["./data/**/*"],
  },
};

export default nextConfig;
