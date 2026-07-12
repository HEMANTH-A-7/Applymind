// sentry.server.config.ts — Server-side error tracking (Node.js/Edge)
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN ?? process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,

  beforeSend(event) {
    // Never send raw user data server-side either
    if (event.user) {
      event.user = { id: event.user.id }; // keep only anonymous ID
    }
    return event;
  },

  enabled: process.env.NODE_ENV === "production",
});
