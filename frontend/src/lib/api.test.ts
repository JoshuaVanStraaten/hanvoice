import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiGet } from "./api";
import { allGoalsDone, goalLabel, goalStates } from "./goals";
import { formatPrice } from "./format";
import type { Plan } from "./types";

function mockFetch(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}), ...response }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api error unwrapping", () => {
  it("unwraps the backend error envelope into ApiError", async () => {
    mockFetch({
      ok: false,
      status: 429,
      json: () =>
        Promise.resolve({
          error: { code: "quota_exceeded", message: "Daily limit reached." },
        }),
    });
    const error = await apiGet("/usage/today").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.status).toBe(429);
    expect(apiError.code).toBe("quota_exceeded");
    expect(apiError.message).toBe("Daily limit reached.");
    expect(apiError.isQuotaExceeded).toBe(true);
  });

  it("keeps a generic message for non-JSON error bodies", async () => {
    mockFetch({
      ok: false,
      status: 502,
      json: () => Promise.reject(new Error("not json")),
    });
    const error = await apiGet("/me").catch((e: unknown) => e);
    const apiError = error as ApiError;
    expect(apiError.code).toBe("http_error");
    expect(apiError.status).toBe(502);
    expect(apiError.isQuotaExceeded).toBe(false);
  });

  it("maps network failures to a friendly offline error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));
    const error = await apiGet("/me").catch((e: unknown) => e);
    const apiError = error as ApiError;
    expect(apiError.code).toBe("network_error");
    expect(apiError.status).toBe(0);
  });
});

describe("goal chips", () => {
  const goals = ["greet the barista", "order the drink", "pay"];

  it("marks backend-confirmed goals done, preserving scenario order", () => {
    const states = goalStates(goals, ["pay", "greet the barista"]);
    expect(states).toEqual([
      { goal: "greet the barista", done: true },
      { goal: "order the drink", done: false },
      { goal: "pay", done: true },
    ]);
    expect(allGoalsDone(states)).toBe(false);
  });

  it("is complete only when every goal is done", () => {
    expect(allGoalsDone(goalStates(goals, goals))).toBe(true);
    expect(allGoalsDone(goalStates([], []))).toBe(false); // no goals ≠ done
  });

  it("ignores completed goals that aren't in the scenario", () => {
    const states = goalStates(goals, ["something else"]);
    expect(states.every((state) => !state.done)).toBe(true);
  });
});

describe("goalLabel", () => {
  it("maps every backend goal key to a human label", () => {
    expect(goalLabel("ordered_drink")).toBe("Ordered a drink");
    expect(goalLabel("stated_destination")).toBe("Told the driver your destination");
    expect(goalLabel("said_nice_to_meet")).toBe("Said nice to meet you");
  });

  it("humanizes unknown keys instead of showing raw snake_case", () => {
    expect(goalLabel("booked_a_table")).toBe("Booked a table");
  });
});

describe("formatPrice", () => {
  const base: Omit<Plan, "id" | "price_usd_cents" | "billing_period"> = {
    name: "x",
    daily_pronunciation_limit: 0,
    daily_conversation_turn_limit: 0,
    daily_llm_token_limit: 0,
    daily_handwriting_limit: 0,
  };

  it("formats free, monthly, and lifetime prices", () => {
    expect(
      formatPrice({ ...base, id: "free", price_usd_cents: 0, billing_period: "none" }),
    ).toEqual({ amount: "$0", cadence: "forever" });
    expect(
      formatPrice({
        ...base,
        id: "premium",
        price_usd_cents: 1499,
        billing_period: "monthly",
      }),
    ).toEqual({ amount: "$14.99", cadence: "per month" });
    expect(
      formatPrice({
        ...base,
        id: "founder",
        price_usd_cents: 6900,
        billing_period: "lifetime",
      }),
    ).toEqual({ amount: "$69", cadence: "once, yours for life" });
  });
});
