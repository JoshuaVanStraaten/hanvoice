import type { Plan } from "./types";

export function formatPrice(plan: Plan): { amount: string; cadence: string } {
  if (plan.price_usd_cents === 0) return { amount: "$0", cadence: "forever" };
  const dollars = plan.price_usd_cents / 100;
  const amount = Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`;
  return {
    amount,
    cadence: plan.billing_period === "lifetime" ? "once, yours for life" : "per month",
  };
}
