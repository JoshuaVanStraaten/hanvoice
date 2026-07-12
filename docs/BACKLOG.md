# HanVoice Backlog — road to the first paying customer

**Source:** full product + technical audit of the live app, 2026-07-12
(Session 1 of 5, `HanVoice_Fable5_Goal_Prompt_v1.1.xml`). Audited on a
390×844 mobile viewport against https://hanvoice.vercel.app with the test
account. **Do not repeat this audit** — append new findings here instead.

Each item: **what · where · impact**. Severity = distance from revenue.

## Critical — nobody can pay / nobody gets in

1. **Stripe not configured.** `Get Premium` on /subscription →
   `POST /api/billing/checkout` 503 → "Payments are not enabled on this
   deployment." Verified live. Every visitor with a card out is a dead end;
   revenue is structurally impossible until this ships. (HANDOVER item 1 —
   products/prices, 4 Fly secrets, webhook.)
2. **Email confirmation gates first use on rate-limited SMTP.** Signup ends at
   "Check your email" (`SignupPage.tsx:45`), but Supabase built-in SMTP allows
   ~3 emails/hour. The 4th signup in any hour never gets the email and is lost
   at the door. Configure custom SMTP (Resend/Postmark) before driving any
   traffic. (HANDOVER item 2.)
3. **Zero analytics.** No GA/PostHog/Plausible, no events, nothing in the
   bundle or code (verified by grep + network log). Can't see visits, funnel
   drop-off, activation, or retention — every later session's decisions would
   be guesses. Add a privacy-light tool (PostHog or Plausible) + a handful of
   funnel events (landing → signup → confirmed → first lesson → first score →
   upgrade click).

## High — actively bleeds conversion or retention

4. **~6 s API cold start on nearly every visit.** Fly scale-to-zero; measured
   5.9 s on `/api/health`. At pre-launch traffic *every* visit is cold: the
   landing pricing section sits on "Loading pricing", first login and first
   audio hang. Cheapest fix: `min_machines_running = 1` (~$2–3/mo); or a
   scheduled keep-warm ping.
5. **No SEO surface at all.** SPA ships an empty `<div id="root">` to
   crawlers; `robots.txt` and `sitemap.xml` are swallowed by the SPA rewrite
   and return the HTML shell (soft-404s, verified); no Open Graph/Twitter
   meta, so shared links (the K-drama fan channel!) render bare. Organic
   acquisition is currently zero-capacity. Fix: static robots/sitemap in
   `frontend/public/`, OG tags in `index.html`, prerender or SSG the landing
   page later.
6. **No social login.** Email+password+confirmation is the highest-friction
   path for a mobile K-pop/K-drama audience — and Google/Apple OAuth
   (Supabase supports both) also sidesteps the SMTP bottleneck in item 2.
7. **No error monitoring.** No Sentry or equivalent; production errors are
   invisible. A broken record button on some Android browser would be
   discovered only by silence. Pairs with item 3.
8. **Handwriting judge fails honest attempts — and write blocks gate
   lessons.** Nemotron-VL-8B scores thin/synthetic strokes near zero (known,
   HANDOVER gotcha); write blocks require ≥60 to pass. A beginner writing ㅏ
   with a finger, decently, and failing repeatedly concludes *they* are bad
   and churns. Config-line model swap per HANDOVER; alternatively lower the
   gate or make write blocks skippable-but-tracked. Was "v2 quality"; it's a
   retention item now that writing gates progress.
9. **Talk has one scenario.** The marquee feature (only "Order an iced
   Americano", ★ difficulty) is exhausted in ~5 minutes. Nobody pays $69
   lifetime for one café chat; scenario depth is the clearest willingness-to-
   pay lever. Content is data (INSERT, no deploy) — cheapest high-impact work
   in the backlog.

## Medium — polish that pays for itself

10. **Goal chips show raw internal keys.** Talk scenario card and session
    header render `ordered_drink`, `stated_size_or_temp`, `said_thanks`
    (verified live). Undermines the marquee feature's credibility; map keys →
    human labels ("Ordered a drink") in data or a small frontend map.
11. **Landing pricing blocks on the cold API.** "Loading pricing" for ~6 s on
    a cold visit (see item 4) for three effectively static tiers. Ship a
    hardcoded fallback that reconciles when the fetch lands.
12. **"Native language" is a free-text field containing `en`.** /settings.
    Confusing to a real user; make it a small select (en/es/ja/zh/…).
13. **Founder-pass holders still see "Get Premium".** /subscription. Clicking
    it would double-charge intent; hide or disable when current plan covers it.
14. **Progress says "No conversations yet" after you've talked to Minji.**
    Only *ended* sessions count, and nothing nudges you to end one. Count
    sessions with ≥1 turn, or add a clear "End conversation" affordance.
15. **593 kB single JS chunk (171 kB gzip).** Build already warns. Mobile-
    first product on mobile networks; route-level code splitting when it's
    worth the complexity — landing page currently pays for the whole app.
    (HANDOVER v2 item; kept here so it isn't lost.)

## Low — noted, not urgent

16. **Pre-migration lesson rollups lack block progress** (test account only —
    café essentials replays from step 1). Real users unaffected; backfill or
    ignore. (HANDOVER item 4.)
17. **No PWA install nudge.** Manifest is installable and the SW is active,
    but nothing invites the user to install; a small post-first-score prompt
    would lift return visits.
18. **Auth UI components are untested** (`AuthLayout`, `AuthContext`,
    `LoginPage` — top of the code-graph `risk_index`, security-relevant,
    0 direct tests). The funnel's front door has no regression net; add a few
    RTL tests when auth is next touched (e.g. item 6).
19. **Existing v2 quality list** (phoneme-level coaching, streaks,
    romanization toggle, audio pre-generation, N+1 lesson queries) — stays in
    HANDOVER item 5; none of it blocks the first customer.

## What's already good (don't fix what isn't broken)

Marketing landing page exists and is strong (hero, demo phrase, 3 features,
pricing, waitlist capture — waitlist posts to a real `/waitlist` endpoint);
auth round-trip, lesson stepper with resume, teaching audio, conversation
loop with live goal tracking, romanization + translation, graceful 404, and
labeled/accessible controls throughout all verified working live. Console was
clean across the whole session except the expected billing 503.
