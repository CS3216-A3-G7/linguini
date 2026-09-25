import type { NextConfig } from "next";
import { movedPosts } from "./data/posts";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async redirects() {
    return Object.entries(movedPosts).map(([from, to]) => ({
      source: `/blog/${from}`,
      destination: `/blog/${to}`,
      permanent: true,
    }));
  },
  images: {
    formats: ["image/avif", "image/webp"],
  },
  outputFileTracingIncludes: {
    "/og": ["./assets/**/*", "./public/photos/**/*", "./public/brand/**/*", "./public/pasta/**/*"],
    "/opengraph-image": ["./assets/**/*", "./public/photos/**/*", "./public/brand/**/*", "./public/pasta/**/*"],
  },
};

export default nextConfig;
