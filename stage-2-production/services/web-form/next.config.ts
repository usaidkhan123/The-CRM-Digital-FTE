import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const apiUrl = process.env.API_GATEWAY_URL || "http://api-gateway:8000";
    return [
      {
        source: "/api/support/:path*",
        destination: `${apiUrl}/support/:path*`,
      },
      {
        source: "/api/tickets",
        destination: `${apiUrl}/tickets`,
      },
    ];
  },
};

export default nextConfig;
