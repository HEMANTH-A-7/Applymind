import type { NextConfig } from "next";
import path from "path";

const isDev = process.env.NODE_ENV === "development";
const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
  transpilePackages: ["three"],

  // ─── Source maps ──────────────────────────────────────────────────
  // NEVER expose source maps in production — they reveal your full source code.
  productionBrowserSourceMaps: false,

  // ─── Turbopack (dev) ──────────────────────────────────────────────
  turbopack: {
    root: path.resolve(__dirname),
  },

  // ─── Environment validation ────────────────────────────────────────
  // Fail build if required env vars are missing in production.
  // This prevents accidental deploy with missing config.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },

  // ─── Security headers ──────────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
          },
          // HSTS — enforced in production (Vercel handles cert)
          ...(isProd ? [{
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          }] : []),
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              // unsafe-eval: required by Three.js + GSAP shader compilation
              // unsafe-inline: required by Next.js inline style injection
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://*.sentry.io",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https:",
              // Allow API + Firebase + Sentry connections
              `connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"} https://*.firebaseio.com https://*.googleapis.com https://*.sentry.io wss://*.firebaseio.com`,
              "worker-src 'self' blob:",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
        ],
      },
      // Cache static assets aggressively
      {
        source: "/_next/static/(.*)",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      // OG image cached 1 week
      {
        source: "/og-image.png",
        headers: [
          { key: "Cache-Control", value: "public, max-age=604800, stale-while-revalidate=86400" },
        ],
      },
    ];
  },

  // ─── Redirects ────────────────────────────────────────────────────
  async redirects() {
    return [
      { source: "/privacy/", destination: "/privacy", permanent: true },
      { source: "/terms/",   destination: "/terms",   permanent: true },
      { source: "/login/",   destination: "/login",   permanent: true },
    ];
  },

  // ─── Webpack: strip source maps in prod, suppress large bundle warnings ───
  webpack(config, { isServer, dev }) {
    if (!dev) {
      // No source maps in client bundle
      config.devtool = false;
    }

    // Suppress "Critical dependency" warning from firebase-admin (server only)
    config.ignoreWarnings = [
      { module: /node_modules\/@firebase/ },
      { module: /node_modules\/firebase/ },
    ];

    return config;
  },
};

// ─── Wrap with Sentry (only in production builds) ──────────────────
// eslint-disable-next-line @typescript-eslint/no-require-imports
const withSentry = isProd
  ? require("@sentry/nextjs").withSentryConfig
  : (c: NextConfig) => c;

export default withSentry(nextConfig, {
  // Sentry build options
  org:                 process.env.SENTRY_ORG,
  project:             process.env.SENTRY_PROJECT,
  silent:              !process.env.CI,
  widenClientFileUpload: true,
  hideSourceMaps:      true,          // ← never expose source maps in prod
  disableLogger:       true,
  automaticVercelMonitors: false,
});
