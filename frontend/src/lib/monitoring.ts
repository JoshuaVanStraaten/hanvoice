/** Sentry error monitoring — env-gated. Without VITE_SENTRY_DSN this is a
 * no-op, so dev and test runs never report. Errors only: tracing and replay
 * stay off to keep the free-tier quota for what matters pre-launch. */

import * as Sentry from "@sentry/react";

const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;

export function initMonitoring(): void {
  if (!dsn) return;
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0,
  });
}
