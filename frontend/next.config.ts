import type { NextConfig } from "next";

// Built as static pages (next build -> out/) that the FastAPI backend serves, so the
// finished system runs as one Python program and needs no Node.js server.
// On Vercel (docs/cloud.md) it is built as a normal Next.js app instead, which forwards the
// API's paths to the backend on Modal (SAPPS_API_URL), so the browser sees one site and the
// session cookie stays first-party.
const shared: NextConfig = {
  trailingSlash: true, // every page becomes folder/index.html
  images: { unoptimized: true },
  poweredByHeader: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

// The headers a careful host sends; Vercel adds HSTS itself.
const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "same-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

function forwardToApi(url: string): NextConfig {
  return {
    ...shared,
    // The API's paths never end in a slash, so Next.js must not add one before forwarding.
    skipTrailingSlashRedirect: true,
    async rewrites() {
      return [
        { source: "/api/:path*", destination: `${url}/api/:path*` },
        { source: "/docs", destination: `${url}/docs` },
        { source: "/openapi.json", destination: `${url}/openapi.json` },
      ];
    },
    async headers() {
      return [{ source: "/:path*", headers: SECURITY_HEADERS }];
    },
  };
}

export default function config(): NextConfig {
  if (process.env.VERCEL) {
    if (!process.env.SAPPS_API_URL) {
      throw new Error("Set SAPPS_API_URL in the Vercel project to the backend's Modal address (docs/cloud.md)");
    }
    return forwardToApi(process.env.SAPPS_API_URL.replace(/\/$/, ""));
  }
  return { ...shared, output: "export" };
}
