import { afterEach, describe, expect, it, vi } from "vitest";

const init = vi.fn();
const capture = vi.fn();
const identify = vi.fn();
const reset = vi.fn();

vi.mock("posthog-js", () => ({
  default: { init, capture, identify, reset },
}));

/** The module reads env at import time, so each test re-imports it fresh. */
async function loadAnalytics() {
  vi.resetModules();
  return import("./analytics");
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

afterEach(() => {
  vi.unstubAllEnvs();
  vi.clearAllMocks();
});

describe("analytics", () => {
  it("is a silent no-op without VITE_POSTHOG_KEY", async () => {
    vi.stubEnv("VITE_POSTHOG_KEY", "");
    const analytics = await loadAnalytics();
    analytics.initAnalytics();
    analytics.track("signup_submitted");
    analytics.identifyUser("user-1");
    analytics.resetAnalytics();
    await flush();
    expect(init).not.toHaveBeenCalled();
    expect(capture).not.toHaveBeenCalled();
  });

  it("initializes once and forwards events when the key is set", async () => {
    vi.stubEnv("VITE_POSTHOG_KEY", "phc_test");
    const analytics = await loadAnalytics();
    analytics.initAnalytics();
    analytics.track("signup_submitted", { plan: "founder" });
    analytics.track("signed_in");
    await flush();
    expect(init).toHaveBeenCalledTimes(1);
    expect(init.mock.calls[0]?.[0]).toBe("phc_test");
    expect(capture).toHaveBeenCalledWith("signup_submitted", { plan: "founder" });
    expect(capture).toHaveBeenCalledWith("signed_in", undefined);
  });

  it("identifies with email and resets on logout", async () => {
    vi.stubEnv("VITE_POSTHOG_KEY", "phc_test");
    const analytics = await loadAnalytics();
    analytics.identifyUser("user-1", "a@b.c");
    analytics.identifyUser("user-2");
    analytics.resetAnalytics();
    await flush();
    expect(identify).toHaveBeenCalledWith("user-1", { email: "a@b.c" });
    expect(identify).toHaveBeenCalledWith("user-2", undefined);
    expect(reset).toHaveBeenCalledTimes(1);
  });
});
