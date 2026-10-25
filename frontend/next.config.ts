import type { NextConfig } from "next";

// Built as static pages (next build -> out/) that the FastAPI backend serves, so the
// finished system runs as one Python program and needs no Node.js server.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true, // every page becomes folder/index.html
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
