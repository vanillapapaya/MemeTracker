import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "r2.memetracker.app" },
      { protocol: "https", hostname: "pbs.twimg.com" },
      { protocol: "https", hostname: "safebooru.org" },
    ],
  },
};

export default nextConfig;
