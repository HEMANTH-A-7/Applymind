// sentry.client.config.ts — Browser error tracking
// This file is loaded in the browser. PII is scrubbed before sending.
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,

  // Performance monitoring
  tracesSampleRate: process.env.NODE_ENV === "production" ? 0.2 : 1.0,

  // Session replays (1% prod, 100% dev on errors)
  replaysSessionSampleRate: 0.01,
  replaysOnErrorSampleRate: 1.0,

  // ─── PII scrubbing — CRITICAL for GDPR compliance ────────────────
  beforeSend(event) {
    // Strip any resume text, job descriptions, or user content
    if (event.extra) {
      delete event.extra.resume_text;
      delete event.extra.jd_text;
      delete event.extra.cover_letter;
    }
    // Redact email from user context
    if (event.user?.email) {
      event.user.email = "[redacted]";
    }
    return event;
  },

  integrations: [
    Sentry.replayIntegration({
      // Mask all text + block all media in replays (GDPR safe)
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  // Only send errors in production
  enabled: process.env.NODE_ENV === "production",
});
