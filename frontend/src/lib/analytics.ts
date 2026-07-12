/** PostHog funnel analytics — env-gated and lazy.
 *
 * Without VITE_POSTHOG_KEY every export is a silent no-op, so dev and test
 * runs stay clean. The SDK is loaded via dynamic import to keep ~50 kB out
 * of the main chunk; callers fire-and-forget and never await analytics.
 * Named funnel events (landing pageview comes free via history_change):
 * signup_submitted → signed_in → lesson_started → attempt_scored →
 * upgrade_clicked.
 */

import type { PostHog } from "posthog-js";

const key = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const host =
  (import.meta.env.VITE_POSTHOG_HOST as string | undefined) || "https://eu.i.posthog.com";

let clientPromise: Promise<PostHog | null> | undefined;

function load(): Promise<PostHog | null> {
  if (!key) return Promise.resolve(null);
  clientPromise ??= import("posthog-js")
    .then(({ default: posthog }) => {
      posthog.init(key, {
        api_host: host,
        capture_pageview: "history_change",
        capture_pageleave: true,
        autocapture: true,
        disable_session_recording: true,
      });
      return posthog;
    })
    // Analytics must never break the app (ad-blockers, offline, CSP).
    .catch(() => null);
  return clientPromise;
}

/** Kick off SDK load + initial pageview. Call once at app start. */
export function initAnalytics(): void {
  void load();
}

export function track(event: string, properties?: Record<string, unknown>): void {
  void load().then((posthog) => posthog?.capture(event, properties));
}

/** Ties events to the account so the funnel survives the signup boundary. */
export function identifyUser(userId: string, email?: string): void {
  void load().then((posthog) => posthog?.identify(userId, email ? { email } : undefined));
}

/** Detach the device from the account on logout (shared devices). */
export function resetAnalytics(): void {
  void load().then((posthog) => posthog?.reset());
}
