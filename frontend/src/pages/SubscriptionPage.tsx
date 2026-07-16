/** Plan comparison + Polar hosted checkout. Handles the ?checkout=success
 * redirect back from Polar; entitlements come from the backend via useMe, so
 * a successful checkout shows up after the webhook lands. */

import { Link, useSearchParams } from "react-router-dom";

import { Button, Card, ErrorNote, Spinner } from "../components/ui";
import { useCheckout, useMe, usePlans } from "../hooks/queries";
import { track } from "../lib/analytics";
import { formatPrice } from "../lib/format";
import type { Plan } from "../lib/types";

const PLAN_PITCH: Record<string, string> = {
  free: "Enough daily practice to build the habit.",
  founder: "Every Premium limit, one payment, forever.",
  premium: "Practice as much as you can talk.",
};

export function SubscriptionPage() {
  const me = useMe();
  const plans = usePlans();
  const checkout = useCheckout();
  const [searchParams] = useSearchParams();
  const checkoutResult = searchParams.get("checkout");

  const currentPlanId = me.data?.plan.id;

  function planCta(plan: Plan) {
    if (plan.id === currentPlanId) return null;
    if (plan.id === "free") return null; // downgrades happen via Polar, not here
    // A Founder Pass already covers Premium limits forever — showing either
    // buy button would be inviting a double charge.
    if (me.data?.has_founder_pass) return null;
    return (
      <Button
        className="w-full"
        disabled={checkout.isPending}
        onClick={() => {
          track("upgrade_clicked", { plan: plan.id });
          checkout.mutate(plan.id as "premium" | "founder");
        }}
      >
        {checkout.isPending ? "Opening checkout…" : `Get ${plan.name}`}
      </Button>
    );
  }

  return (
    <div className="space-y-4">
      <header>
        <Link to="/settings" className="text-sm font-semibold text-taegeuk-blue">
          ← Profile
        </Link>
        <h1 className="text-2xl font-bold">Subscription</h1>
      </header>

      {checkoutResult === "success" && (
        <Card className="border-jade/40">
          <p className="text-sm" role="status">
            <span className="font-semibold text-jade">Payment received.</span> Your new
            limits activate as soon as Polar confirms — usually within seconds.
          </p>
        </Card>
      )}

      {checkout.isError && (
        <ErrorNote error={checkout.error} retry={() => checkout.reset()} />
      )}

      {(me.isPending || plans.isPending) && <Spinner label="Loading plans" />}
      {plans.isError && <ErrorNote error={plans.error} retry={() => void plans.refetch()} />}

      {plans.isSuccess && (
        <div className="grid gap-4 sm:grid-cols-3">
          {plans.data.map((plan) => {
            const { amount, cadence } = formatPrice(plan);
            const isCurrent = plan.id === currentPlanId;
            return (
              <Card
                key={plan.id}
                className={`flex flex-col gap-3 ${
                  isCurrent ? "border-taegeuk-blue ring-1 ring-taegeuk-blue" : ""
                }`}
              >
                <div className="flex items-baseline justify-between">
                  <h2 className="font-bold">{plan.name}</h2>
                  {isCurrent && (
                    <span className="rounded-full bg-taegeuk-blue px-2.5 py-0.5 text-[11px] font-semibold text-white">
                      Current plan
                    </span>
                  )}
                </div>
                <p>
                  <span className="text-3xl font-bold">{amount}</span>{" "}
                  <span className="text-sm text-ink-soft">{cadence}</span>
                </p>
                <p className="text-sm text-ink-soft">{PLAN_PITCH[plan.id] ?? ""}</p>
                <ul className="space-y-1 text-sm">
                  <li>{plan.daily_pronunciation_limit} pronunciation checks a day</li>
                  <li>{plan.daily_conversation_turn_limit} conversation turns a day</li>
                  <li>{plan.daily_handwriting_limit} handwriting checks a day</li>
                </ul>
                <div className="mt-auto">{planCta(plan)}</div>
              </Card>
            );
          })}
        </div>
      )}

      {me.data?.has_founder_pass && (
        <p className="text-center text-sm text-ink-soft">
          You hold a Founder Pass — thank you for backing HanVoice early. 감사합니다!
        </p>
      )}
    </div>
  );
}
