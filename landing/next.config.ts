import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    formats: ["image/avif", "image/webp"],
  },
  outputFileTracingIncludes: {
    "/og": ["./assets/**/*", "./public/photos/**/*", "./public/brand/**/*", "./public/pasta/**/*"],
    "/opengraph-image": ["./assets/**/*", "./public/photos/**/*", "./public/brand/**/*", "./public/pasta/**/*"],
  },
};

export default nextConfig;
