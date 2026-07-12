/** Public landing page. The hero stages the product's defining moment — a
 * Korean phrase said out loud and scored — using the real ScoreRing and the
 * signature speak ring. Pricing renders from a hardcoded fallback immediately
 * and reconciles against the public `plans` table when the fetch lands; the
 * waitlist form captures visitors who aren't ready to sign up. */

import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { useJoinWaitlist, usePlans } from "../hooks/queries";
import { formatPrice } from "../lib/format";
import type { Plan } from "../lib/types";
import { Button, Card, ScoreRing } from "../components/ui";

const PLAN_PITCH: Record<string, string> = {
  free: "Enough daily practice to build the habit.",
  founder: "Every Premium limit, one payment, forever. Early-supporter pricing.",
  premium: "Practice as much as you can talk.",
};

/** Static mirror of the `plans` table (price-ascending, like usePlans) so
 * pricing paints immediately on a cold visit; the live fetch reconciles any
 * drift when it lands. Update alongside the plans seed if prices change. */
const FALLBACK_PLANS: Plan[] = [
  {
    id: "free",
    name: "Free",
    price_usd_cents: 0,
    billing_period: "none",
    daily_pronunciation_limit: 20,
    daily_conversation_turn_limit: 10,
    daily_llm_token_limit: 20000,
    daily_handwriting_limit: 10,
  },
  {
    id: "premium",
    name: "Premium",
    price_usd_cents: 1499,
    billing_period: "monthly",
    daily_pronunciation_limit: 200,
    daily_conversation_turn_limit: 150,
    daily_llm_token_limit: 300000,
    daily_handwriting_limit: 100,
  },
  {
    id: "founder",
    name: "Lifetime Founder Pass",
    price_usd_cents: 6900,
    billing_period: "lifetime",
    daily_pronunciation_limit: 200,
    daily_conversation_turn_limit: 150,
    daily_llm_token_limit: 300000,
    daily_handwriting_limit: 100,
  },
];

function PlanCard({ plan }: { plan: Plan }) {
  const featured = plan.id === "founder";
  const { amount, cadence } = formatPrice(plan);
  return (
    <Card
      className={`flex flex-col gap-3 ${featured ? "border-taegeuk-blue ring-1 ring-taegeuk-blue" : ""}`}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="font-bold">{plan.name}</h3>
        {featured && (
          <span className="rounded-full bg-taegeuk-blue px-2.5 py-0.5 text-[11px] font-semibold text-white">
            Best value
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
      <Link to="/signup" className="mt-auto">
        <Button className="w-full" variant={featured ? "primary" : "quiet"}>
          {plan.id === "free" ? "Start free" : "Sign up, then upgrade"}
        </Button>
      </Link>
    </Card>
  );
}

function WaitlistForm() {
  const [email, setEmail] = useState("");
  const waitlist = useJoinWaitlist();

  function submit(event: FormEvent) {
    event.preventDefault();
    if (email) waitlist.mutate(email);
  }

  if (waitlist.isSuccess) {
    return (
      <p className="text-sm font-semibold text-jade" role="status">
        You&apos;re on the list — the phrase card is on its way to your inbox.
      </p>
    );
  }

  return (
    <form onSubmit={submit} className="flex w-full max-w-md gap-2">
      <label className="sr-only" htmlFor="waitlist-email">
        Email address
      </label>
      <input
        id="waitlist-email"
        type="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="you@example.com"
        className="min-w-0 flex-1 rounded-full border border-line bg-paper-raised px-4 py-2.5 text-sm placeholder:text-ink-soft/70"
      />
      <Button type="submit" disabled={waitlist.isPending}>
        {waitlist.isPending ? "Joining…" : "Get updates"}
      </Button>
      {waitlist.isError && (
        <p className="w-full text-xs text-taegeuk-red" role="alert">
          That didn&apos;t go through — check the address and try again.
        </p>
      )}
    </form>
  );
}

/** The hero demo: the café phrase as it looks mid-practice, already scored. */
function PhraseDemo() {
  return (
    <Card className="mx-auto w-full max-w-md space-y-4 text-center">
      <p className="text-xs font-semibold tracking-wide text-ink-soft uppercase">
        Lesson 3 · At the café
      </p>
      <p className="hangul-display text-3xl" lang="ko">
        아이스 아메리카노 주세요
      </p>
      <p className="text-sm text-ink-soft">
        a-i-seu a-me-ri-ka-no ju-se-yo · “One iced americano, please.”
      </p>
      <div className="flex items-center justify-center gap-6">
        <Link
          to="/signup"
          aria-label="Try saying this phrase — start free"
          className="speak-ring-active flex size-16 items-center justify-center rounded-full bg-taegeuk-red text-white transition-colors hover:bg-taegeuk-red-deep"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0" />
            <path d="M12 18v3" />
          </svg>
        </Link>
        <ScoreRing score={87} label="Your score" />
      </div>
    </Card>
  );
}

const FEATURES: Array<{ hangul: string; title: string; body: string; speak: boolean }> = [
  {
    hangul: "발음",
    title: "Your pronunciation, actually scored",
    body: "Every phrase you speak gets a 0–100 score from professional speech assessment — you know you're understandable before you need to be.",
    speak: true,
  },
  {
    hangul: "대화",
    title: "Rehearse the real situations",
    body: "Order at a café, take a taxi, haggle at a market, introduce yourself — with an AI partner who stays in character and tracks whether you got what you asked for.",
    speak: true,
  },
  {
    hangul: "쓰기",
    title: "Start reading Hangul in a weekend",
    body: "Guided lessons with handwriting checks turn menus and signs from noise into words.",
    speak: false,
  },
];

export function LandingPage() {
  const plans = usePlans();

  return (
    <div className="min-h-dvh bg-paper">
      <header className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between px-4">
        <span className="text-lg font-bold tracking-tight">
          <span className="text-taegeuk-red">한</span>
          <span className="text-taegeuk-blue">Voice</span>
        </span>
        <Link to="/login" className="text-sm font-semibold text-taegeuk-blue">
          Log in
        </Link>
      </header>

      <main className="mx-auto w-full max-w-3xl space-y-16 px-4 pt-10 pb-16">
        {/* Hero */}
        <section className="space-y-6 text-center">
          <p className="text-xs font-semibold tracking-widest text-taegeuk-red uppercase">
            말하기 · Speaking-first Korean
          </p>
          <h1 className="hangul-display mx-auto max-w-xl text-4xl sm:text-5xl">
            Speak Korean before you land in Seoul.
          </h1>
          <p className="mx-auto max-w-lg text-ink-soft">
            Learn to read Hangul and say the phrases your trip actually needs — with real
            pronunciation scoring and an AI you can rehearse café, taxi, and market
            conversations with, out loud.
          </p>
          <div className="flex justify-center gap-3">
            <Link to="/signup">
              <Button>Start free</Button>
            </Link>
            <a href="#pricing">
              <Button variant="quiet">See pricing</Button>
            </a>
          </div>
          <PhraseDemo />
        </section>

        {/* Features — labeled by the Korean words you'll actually learn. */}
        <section aria-labelledby="features-heading" className="space-y-4">
          <h2 id="features-heading" className="text-center text-2xl font-bold">
            Three ways to practice
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card key={feature.hangul} className="space-y-2">
                <p
                  className={`hangul-display text-2xl ${feature.speak ? "text-taegeuk-red" : "text-taegeuk-blue"}`}
                  lang="ko"
                >
                  {feature.hangul}
                </p>
                <h3 className="font-bold">{feature.title}</h3>
                <p className="text-sm text-ink-soft">{feature.body}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* Pricing — fallback paints instantly, live plans table reconciles.
            No spinner, no error state: a marketing page never says "loading
            pricing" or shows a fetch error for three static tiers. */}
        <section id="pricing" aria-labelledby="pricing-heading" className="space-y-4">
          <h2 id="pricing-heading" className="text-center text-2xl font-bold">
            Pricing
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {(plans.data ?? FALLBACK_PLANS).map((plan) => (
              <PlanCard key={plan.id} plan={plan} />
            ))}
          </div>
        </section>

        {/* Waitlist — the GTM lead magnet (docs/GTM.md §4); delivery is a
            manual Resend broadcast, no automation behind this form. */}
        <section className="flex flex-col items-center gap-3 text-center">
          <h2 className="text-xl font-bold">Trip booked but not ready yet?</h2>
          <p className="max-w-md text-sm text-ink-soft">
            Get the free <strong>Seoul Survival Phrase Card</strong> — the trip phrases from
            our lessons with pronunciation tips — plus the founder-launch discount when we
            open the doors.
          </p>
          <WaitlistForm />
        </section>
      </main>

      <footer className="space-y-2 border-t border-line py-6 text-center text-xs text-ink-soft">
        <p lang="ko" className="hangul-display mb-1 text-sm text-ink">
          오늘도 화이팅!
        </p>
        <p>HanVoice · Speak Korean out loud.</p>
        <nav className="flex justify-center gap-4">
          <Link to="/terms" className="hover:text-taegeuk-blue">
            Terms
          </Link>
          <Link to="/privacy" className="hover:text-taegeuk-blue">
            Privacy
          </Link>
          <Link to="/refunds" className="hover:text-taegeuk-blue">
            Refunds
          </Link>
        </nav>
      </footer>
    </div>
  );
}
