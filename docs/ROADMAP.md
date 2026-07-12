# HanVoice Roadmap — road to the first paying customer

**Created:** 2026-07-12 (Session 2 of 5) · **Sources:** `docs/BACKLOG.md`
items 1–26 (Session 1 product/tech audit + Session 2 educational audit).
Backlog item numbers in parentheses.

**Decision rule applied to every item:** *will this materially increase the
probability of the first paying customer?* If the answer needed a story
longer than one sentence, the item went to Future or the NOT list.

---

## Immediate — before driving any traffic (~2 weeks)

Revenue is structurally impossible and the front door leaks; fix both, then
make the marquee feature worth paying for. Nothing else jumps this queue.

1. **Billing activation — now Paddle, not Stripe** (1) — ⚙ CODE DONE
   (2026-07-12, session 4): full Paddle Billing rewrite shipped (`f4bd0d9`)
   — backend serves Paddle.js overlay config from `/billing/checkout`,
   webhook verifies Paddle-Signature and grants founder pass /
   subscription with price-id cross-checks; frontend opens the overlay
   via `@paddle/paddle-js`. **Session 4b: sandbox E2E VERIFIED** — real
   overlay checkout on hanvoice.app with a test card, webhook
   signature-verified, founder pass granted in the live DB (row id 2).
   Production currently runs sandbox billing (`PADDLE_ENV=sandbox` on
   Fly) on purpose. **Only remaining step: go-live after Paddle approves
   the account (still in review)** — live products + tokens + default
   payment link, then swap the five Fly secrets. Click-by-click in
   HANDOVER.md.
2. **Custom SMTP** (2) — ✅ DONE (2026-07-12, session 3): Resend via
   joshuavanstraaten.com wired into Supabase auth, email rate limit
   raised to 30/hr, live-verified (reset mail delivered to inbox in
   seconds). Mirrored in `supabase/config.toml` — a config push now
   requires `RESEND_API_KEY` in the shell, by design.
3. **Analytics + funnel events** (3) — ✅ DONE (2026-07-12, session 3b):
   PostHog EU live and verified — key in Vercel, baked into the deployed
   bundle, events observed reaching eu.i.posthog.com with 200s.
4. **Kill the cold start** (4) — ✅ DONE (2026-07-12, session 3):
   `min_machines_running = 1` deployed; warm `/api/health` measured 0.54 s
   (was 5.9 s cold).
5. **Error monitoring** (7) — ✅ DONE (2026-07-12, session 3b): Sentry
   live on both stacks; test errors confirmed in both project dashboards
   (`hanvoice-frontend`, `hanvoice-api`).
6. **Handwriting judge swap** (8) — ✅ DONE (2026-07-12, session 3):
   `meta/llama-3.2-90b-vision-instruct`, benchmarked against 4 rivals,
   verified live (honest ㅏ now scores 70; old judge gave 0).
7. **3–4 new Talk scenarios matching existing Speak lessons** (9, 26) —
   ✅ DONE (2026-07-12, session 4): first-meeting, restaurant-lunch,
   taxi-to-hotel, market-shopping inserted into the live DB (5 published
   scenarios total), mirrored in `supabase/seed.sql`, canonical prompts
   in `prompts/scenarios/`. 12 new goal patterns in `services/goals.py`
   deployed to Fly. Live-verified: all four openers valid + TTS audio;
   typed turn 명동까지 가 주세요 detected `stated_destination`.
8. **Conversion polish batch** (5-lite, 10, 11) — ✅ DONE (2026-07-12,
   session 5): `goalLabel()` human labels for all 15 goal keys (Talk cards
   + session chips), hardcoded `FALLBACK_PLANS` pricing on the landing
   page (reconciles against the live plans table), OG/Twitter tags in
   `index.html` + static robots.txt/sitemap.xml in `frontend/public/` —
   all URLs https://hanvoice.app. Deployed and live-verified via curl
   (real robots/sitemap content types, OG tags in served HTML, labels +
   fallback present in the live bundle).
   (13 — hide "Get Premium" for founder-pass holders — ✅ DONE 2026-07-12.)

18. **GTM landing copy swap** (27) — ✅ DONE (2026-07-12, session 7):
    hero headline/subhead + the three feature cards swapped to the GTM §2
    trip-prep copy, and `index.html` meta/OG/Twitter descriptions aligned.
    Deployed to Vercel and live-verified (strings confirmed in served HTML
    + production bundle).
19. **GTM waitlist offer swap** (28) — ✅ DONE (2026-07-12, session 7):
    waitlist section now offers the free Seoul Survival Phrase Card +
    founder-launch discount; success message promises the card. The card
    itself exists (`docs/content/week-01/seoul-survival-phrase-card.html`,
    print-to-PDF; phrases sourced from `supabase/seed.sql`). Delivery
    stays manual via Resend.

**→ Immediate after session 7 = item 1's go-live founder steps (wait on
Paddle's approval email) + running the content engine
(`docs/CONTENT_ENGINE.md`, week-01 batch in `docs/content/week-01/`).**
The 14-day first-customer play in `docs/GTM.md` §5 sequences the money-ask
after that email (reservation fallback if it's late). No engineering items
remain in Immediate.

*Challenged and deliberately NOT immediate:* **landing page** — Session 1
judged it strong; only OG tags ship now. **Retention mechanic** — with zero
traffic there is nobody to retain yet; it leads Next Month instead, before
any paid acquisition. **Social login** — real friction, but SMTP + Stripe
matter more this sprint; it leads Next Month's funnel work.

## Next Month — make it genuinely teach and retain

The educational audit's verdict: strong Hangul pedagogy, then a cliff.
These items close the honesty gap between "learn Korean" and what the app
actually delivers — which is what converts a curious visitor into a
subscriber rather than a one-weekend tourist.

9. **Complete the Hangul course** (20) — 2 lessons (aspirated + tense
   consonants; compound vowels) inserted before `read-and-say-it`, fixing
   the untaught-letter bug (커피/김치/주세요). *Payoff: the course's core
   promise — "you can read Korean" — becomes true.*
10. **Review deck + streak + install nudge** (22, 17) — passed phrases
    resurface on fixed 1/3/7-day intervals; visible streak; PWA install
    prompt after first score. *Payoff: a Day-7 exists at all; a monthly
    subscription needs a habit to bill against.*
11. **Survival grammar + numbers micro-lessons** (24, 25) — sino-Korean
    numbers/prices, 이에요/예요, 네/아니요, the NOUN + 주세요 pattern; one
    intro explain block per Speak lesson. ~5 content INSERTs. *Payoff:
    memorized strings become generative language; the learner can finally
    understand the answer to 얼마예요?.*
12. **Listening blocks** (23) — quiz payload variant with an audio prompt
    (hear → choose meaning); "hide translation" toggle in Talk. *Payoff:
    trains the one modality conversation actually requires; makes Talk a
    listening exercise instead of a reading exercise.*
13. **Google social login** (6) — *Payoff: lowest-friction path for a
    mobile K-content audience, and every OAuth signup bypasses SMTP risk.*

## Next Quarter — depth that justifies the subscription

14. **Vocabulary to ~150–200 words** (21) — ~8–10 new Speak lessons themed
    to existing/new scenarios. *Payoff: pushes the content wall from day 3
    past week 4 — past the first monthly renewal.*
15. **Scenario difficulty tiers** (9, 23) — ★★ variants of existing scenes:
    romanization hidden, stricter goals, faster Minji. *Payoff: replay value
    from the same content investment; a visible progression ladder.*
16. **Landing prerender/SSG + route code splitting** (5, 15) — *Payoff:
    organic acquisition capacity and mobile load times — worth doing once
    analytics shows traffic to optimize.*
17. **Auth component tests** (18) — alongside the social-login work, while
    that code is open. *Payoff: regression net for the funnel's front door.*

## Future — real, but not on the path to customer #1

Phoneme-level pronunciation coaching (Azure streaming SDK) · raw-audio
persistence for progress review · audio pre-generation into Storage ·
N+1 lesson-query batching · richer gamification beyond a streak ·
native-number lesson and other post-survival grammar · backfill of
pre-migration test-account progress (16 — affects nobody real).

## What we will NOT do, and why

- **A full SRS engine (SM-2, ease factors, leech handling).** Fixed 1/3/7
  intervals capture most of the retention value at ~5% of the complexity.
  Revisit only if review-deck analytics show it's insufficient.
- **CMS / admin UI for content.** Authoring is SQL INSERTs by one founder;
  a CMS is building software for an employee we don't have.
- **Hard lesson locking.** Design decision stands (frustration > discipline
  for a beginner app); soft guidance only.
- **Native iOS/Android apps.** The PWA installs and works; no evidence the
  wrapper is what blocks a purchase. Enormous cost, zero proven payoff.
- **More AI providers or model upgrades** beyond the one-line handwriting
  judge swap. The current stack is verified live and paid for.
- **Romanization profile toggle, leaderboards, community features.** No
  plausible story connecting any of them to customer #1.
- **Rebuilding the landing page.** Session 1 audited it as strong; touching
  it burns the budget the scenarios need.
- **Any Immediate-tier feature building beyond this list** — Sessions 3+
  (v1.3 prompts) implement; this document is the contract for what.
