# HanVoice — Session Handover

**Updated:** 2026-07-16 (session 8) · **Branch:** `main` · **Status: POLAR BILLING — ACCOUNT LIVE + CODE DONE; DEPLOY + E2E PENDING (see Polar section).** Session 8: Paddle rejected twice → Polar chosen (`_os/DECISIONS.md`), account created/KYC'd/approved same day, products + webhook + token provisioned via API, full billing rewrite shipped (backend 124 tests / frontend 42 tests green). Next founder/session actions are the 4 numbered steps in the Polar section.

**Previous status (session 7):** DEPLOYED; CONTENT ENGINE BUILT + GTM COPY LIVE. Session 7 (v1.5) shipped ROADMAP Immediate 18–19 and the content machine. **(a) Copy live on hanvoice.app** (deployed `vercel deploy --prod`, dpl_C2JaadeFTKcyzjjAEfu2sfcvcxES, strings verified in served HTML + bundle): hero/features in `frontend/src/pages/LandingPage.tsx` swapped to GTM §2 trip-prep copy ("Speak Korean before you land in Seoul"), waitlist section now offers the free **Seoul Survival Phrase Card** + launch discount (GTM §4), `frontend/index.html` meta/OG/Twitter aligned. eslint/tsc/42 tests green. **(b) `docs/CONTENT_ENGINE.md`**: 3 formats kept (tourist-phrase TikTok demo, pronunciation tip/challenge TikTok, Reddit trip-value post — K-drama/K-pop/slang/daily killed as wrong-segment), copy-paste LLM prompt templates per format, ~5 h/week schedule (Sunday 3 h batch), funnel table (all build steps ✅; remaining ⚠ are founder actions from GTM §5), Sunday 15-min KPI ritual + review log. **(c) `docs/content/week-01/`**: the phrase card (`seoul-survival-phrase-card.html` — open in browser → print to PDF; all phrases verbatim from `supabase/seed.sql`, nothing invented) + 5 ready pieces mapped to GTM days 3–8 (3 TikTok scripts, 1 r/koreatravel post, 1 waitlist email) — see its README for posting order. **No engineering left in Immediate. Open threads: (1) founder runs the 14-day play Day 0/1 (GTM §5): fresh-signup funnel check, print card PDF, create TikTok account; (2) Paddle go-live steps when the approval email arrives (Paddle section below; until then every money-ask is the reservation fallback, GTM §5); (3) weekly loop = produce/post from CONTENT_ENGINE.md, v1.3 build sessions only for Next-Month roadmap items.**

## What exists

The full application (M1–M10 of `docs/superpowers/plans/2026-07-03-hanvoice-full-app.md`)
plus the **real curriculum** (`docs/superpowers/plans/2026-07-04-lesson-blocks-curriculum.md`,
design in `docs/superpowers/specs/2026-07-04-lesson-blocks-curriculum-design.md`):
FastAPI backend (112 tests; ruff + strict mypy clean), React PWA frontend
(42 tests; eslint + tsc clean), Docker images smoke-tested, CI workflow written.
See `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`, `docs/schema.md`.

**Curriculum architecture (new):** lessons are ordered `lesson_blocks`
(`explain | speak | write | quiz`, JSONB payload; speak blocks FK to
`lesson_phrases` so the whole pronunciation stack is reused). Per-block pass
state in `lesson_block_progress` (backend-written; speak/write pass only via
scored attempts ≥ 60, explain/quiz via `POST /lessons/blocks/{id}/complete`).
`lesson_progress.phrases_completed` → `blocks_completed`. The lesson page is a
stepper player that resumes at the first unpassed block; the standalone Write
tab still works (canvas extracted to `HangulCanvas`).

## Live environment

- **Production (deployed 2026-07-05, full post-deploy checklist passed;
  domain added 2026-07-12):**
  - Frontend: **https://hanvoice.app** — canonical since 2026-07-12
    (registered at Cloudflare Registrar, DNS = Cloudflare zone, apex CNAME
    `844769263b8c30c1.vercel-dns-017.com` with proxy **DNS-only** — never
    turn the orange cloud on, it breaks Vercel certs).
    **https://hanvoice.vercel.app** still works as alias. (Vercel project
    `hanvoice`, `frontend/vercel.json` SPA rewrites; `VITE_*` vars set as
    production env — Vite bakes them at build, so changing one requires a
    redeploy.) `VITE_POSTHOG_KEY` + `VITE_SENTRY_DSN` are set and live-verified.
  - Backend: **https://hanvoice-api.fly.dev** (Fly app `hanvoice-api`, region
    `lhr` — Dublin had no capacity; `backend/fly.toml`; single machine kept
    warm via `min_machines_running = 1`). Secrets: Supabase, Azure, NVIDIA +
    `APP_ENV`/`LOG_LEVEL` + `SENTRY_DSN` (verified: test event reached the
    hanvoice-api Sentry project) + `CORS_ORIGINS` =
    `https://hanvoice.app,https://hanvoice.vercel.app` (both preflight-verified)
    and `FRONTEND_URL` = `https://hanvoice.app`. `STRIPE_*` unset → billing
    503s by design (Paddle rewrite pending).
  - GitHub: **https://github.com/JoshuaVanStraaten/hanvoice** (private). CI
    green (first run needed `python -m pytest`, `fc06554`).
  - Verified live: login, cross-origin usage read (CORS), scored pronunciation
    attempt (79.6) metering usage, block teaching-audio endpoint, service
    worker active + installable manifest.
  - Auth email redirects (`45acdc8`, re-pointed 2026-07-12): Supabase
    `site_url` → **https://hanvoice.app**, allowlist = hanvoice.app +
    hanvoice.vercel.app + localhost:5173 (pushed via `supabase config push`;
    `supabase/config.toml` mirrors the remote auth config — keep it that way,
    a push syncs the whole [auth] block and needs `RESEND_API_KEY` in the
    shell), and `signUp` passes `emailRedirectTo` per origin. Live-verified:
    reset mail lands from hello@hanvoice.app with
    `redirect_to=https://hanvoice.app`.
- **Supabase project `hanvoice`** (`mxibibkcaarltsbkomvm`, eu-west-1, free tier) —
  migrated + seeded. `frontend/.env` and `backend/.env` are wired (gitignored).
- **Content:** 13 lessons in two sections — **"Read & write Hangul"** (8 lessons,
  62 blocks: what-is-hangul → vowels → consonants → building syllables → more
  letters → batchim → sound changes → reading + 해요체) and **"Speak"** (the 5
  phrase lessons as speak-block units) — plus **5 conversation scenarios**
  (since session 4): cafe-iced-americano, first-meeting, restaurant-lunch,
  taxi-to-hotel ★★, market-shopping ★★ — one per Speak lesson, Minji plays
  every role. Canonical prompts in `prompts/scenarios/*_v1.md`. Content is
  data — new lessons/scenarios are an INSERT, no deploy (but new **goal
  patterns** live in `backend/app/services/goals.py` and DO need a deploy).
  `supabase/seed.sql` mirrors the live content.
- **Azure Speech** (northeurope, F0): pronunciation scoring, STT for conversation
  turns, Korean neural TTS (SunHi). **NVIDIA**: Llama barista chat + Nemotron-VL
  handwriting vision. All verified live, in-browser and via API.
- **Test account:** `joshuavanstraaten100+hanvoice-test@gmail.com` /
  `hanvoice-test-1234` (email-confirmed via SQL; holds a manually-granted founder
  pass → 200/day quotas). The founder entitlement path is therefore live-tested.
- User's other Supabase project **pettlo-poc was paused** to free the free-tier
  slot — don't unpause/delete without asking.

## Polar billing: LIVE ACCOUNT + CODE DONE (2026-07-16) — deploy + E2E remain

**Paddle is dead** — rejected twice (AI-assessment AUP), even after the copy
reframe. Decision + full rationale: `_os/DECISIONS.md` 2026-07-16. **Polar
(polar.sh) account is APPROVED and LIVE** (same-day: signup, org `hanvoice`
id `9e5bb4d5-f004-4ce0-b352-24f5a5e1cee7`, KYC via SA driver's license,
Capitec payout account via SWIFT `CABLZAJJ`). Products created via API:
Founder Pass $69 one-time (`ff50af3e-…`, price `33f416bd-…`), Premium
$14.99/mo (`4076c327-…`, price `8f3bafdb-…`). Webhook endpoint
`be4a23aa-…` → `https://hanvoice-api.fly.dev/api/billing/webhook`
(order.paid/refunded + subscription.* events). Org token
`hanvoice-backend` (expires 2027-07-16). All five `POLAR_*` values in
`backend/.env`; live checkout verified rendering with real card fields.

**Code (plan: `docs/superpowers/plans/2026-07-16-polar-billing-rewrite.md`):**
backend creates the checkout session server-side (`POST /v1/checkouts/`,
metadata `{user_id, plan}` is server-set = trusted; product id still
cross-checked in the webhook), returns `{url}`; frontend redirects
(`lib/paddle.ts` deleted, `@paddle/paddle-js` uninstalled). Webhook is
**standard-webhooks** (headers `webhook-id/-timestamp/-signature`, signed
`{id}.{ts}.{body}`, HMAC-SHA256 base64, `v1,` prefix, 5-min tolerance —
NOT Paddle's `ts;h1`). Signature verify accepts both key interpretations
(literal secret string per Polar docs, base64-decoded per spec). Polar
statuses kept: trialing/active/past_due/canceled; anything else
(incomplete/unpaid/revoked) → canceled. 124 backend tests, ruff + strict
mypy clean; eslint + tsc + 42 frontend tests green.

**DEPLOYED + E2E PASSED (2026-07-16, same session):** Fly deployed with
POLAR_* secrets (PADDLE_* removed); Vercel deployed + aliased (live bundle
has zero Paddle references). Production E2E: fresh account → app buy
button → backend-created Polar checkout → 100% discount → $0 purchase →
**webhook signature-verified and processed on the first real delivery →
`founder_pass_purchases` id=3 (provider=polar) → founder UI live.** The
E2E discount was deleted afterwards. Second E2E account
`joshuavanstraaten100+polar-e2e@gmail.com` / `polar-e2e-test-1234` holds a
founder pass (like the original test account). Premium subscription path
is unit-tested but not click-tested (same as Paddle era) — optional.

**Remaining: flip GTM copy from reservation-fallback to the real $69
money-ask — GTM §5's gate is OPEN. Billing is LIVE.**

**Polar gotchas:** dashboard form buttons don't submit on click — press
Enter inside a form field instead (token + product forms both). Org
settings country is still unset (harmless; payout account carries the
banking country). The old sandbox Paddle account still exists — ignore it.

## OLD Paddle notes (dead — kept one session for reference)

**Architecture (`f4bd0d9`):** client-opened Paddle.js **overlay checkout** +
server-verified webhook. `POST /billing/checkout` (authed) returns
`{environment, client_token, price_id, custom_data: {user_id, plan}, email,
success_url}`; the frontend (`lib/paddle.ts`) initializes Paddle.js with that
and opens the overlay. No Paddle API key server-side, no `VITE_*` billing
vars — changing billing config never needs a Vercel redeploy.
`POST /billing/webhook` verifies `Paddle-Signature` (ts/h1 HMAC-SHA256 of
`{ts}:{raw_body}`, 60 s replay window) and handles `transaction.completed`
(founder pass; ignores subscription-linked transactions) and
`subscription.*` (premium upsert; `paused`/unknown statuses map to
`canceled`, `scheduled_change.action` → `cancel_at_period_end`). Because
`custom_data` originates client-side, **grants cross-check the purchased
price id against the plan label** — a tampered label buys nothing.
Backend env (all in `backend/.env`, currently empty → 503):
`PADDLE_ENV` (sandbox|production), `PADDLE_CLIENT_TOKEN`,
`PADDLE_WEBHOOK_SECRET`, `PADDLE_PRICE_PREMIUM`, `PADDLE_PRICE_FOUNDER`.

**Sandbox: DONE + E2E VERIFIED (2026-07-12, session 4b).** Sandbox account
exists; products/prices created (founder `pri_01kxbnp67x33e1xc6n1hyz6xvm`
$69 one-time, premium `pri_01kxbntzmq7eqfj89zx1da1ps7` $14.99/mo, both max
quantity 1); client token + webhook secret minted. The five `PADDLE_*`
sandbox values are in `backend/.env` AND set as Fly secrets
(`PADDLE_ENV=sandbox` — production currently runs SANDBOX billing on
purpose until go-live). Frontend with the overlay code deployed to Vercel
(`index-vZDGK0Lh.js`). **Full loop verified with a real sandbox checkout:**
overlay opened on hanvoice.app, test-card payment, webhook
signature-verified, `founder_pass_purchases` row `id=2` written
(`provider=paddle`, `txn_01kxbvwr44hrz9xeqdbay2ad1j`, 6900 cents), buy
buttons hidden, founder-pass footer shown. Premium subscription checkout
not yet click-tested (handler unit-tested; optional: repeat with a second
fresh account).

Hard-won sandbox facts (apply to LIVE too):
- Checkout FAILS with a generic "Something went wrong" overlay until BOTH
  are set in the dashboard: **Checkout → Checkout settings → Default
  payment link** (= `https://hanvoice.app/subscription`) AND the website
  added under **Request website approval** (sandbox approves instantly).
- The webhook **Secret key** is NOT the `ntfset_…` destination id shown in
  the list — open the destination's ⋯ → Edit destination and copy the
  `pdl_ntfset_…_…` value (contains `+`/`/` — quote it in shells).
- Payment methods enabled in sandbox Checkout settings: PayPal, Apple Pay,
  Google Pay, Bancontact + regionals — mirror this in live.

**Founder: go-live (ONLY after Paddle approval email):** in the LIVE
dashboard: create the two products/prices (same specs), client-side token
(no `test_` prefix), notification destination →
`https://hanvoice-api.fly.dev/api/billing/webhook` with
`transaction.completed` + `subscription.created/updated/canceled/paused/resumed`,
set the **default payment link** + payment methods (see facts above;
domain approval comes with account approval). Then from `backend/`:
`flyctl secrets set PADDLE_ENV=production PADDLE_CLIENT_TOKEN=… 'PADDLE_WEBHOOK_SECRET=…' PADDLE_PRICE_PREMIUM=… PADDLE_PRICE_FOUNDER=…`
(quotes around the webhook secret — it contains `+`/`/`). Machine restarts
itself. Verify with a real $69 self-purchase (money returns via Paddle
payout) or a small live smoke + immediate refund via the Paddle dashboard.

## Founder account setup: COMPLETE (session 3b, 2026-07-12)

Every account is live and verified with evidence. Per-account end state:

- **Domain: hanvoice.app** — bought at Cloudflare Registrar (~$14/yr,
  auto-renew on). Attached to Vercel project `hanvoice` (verified, serving
  200 with valid cert), apex CNAME `844769263b8c30c1.vercel-dns-017.com`
  (Vercel's newer edge — the "DNS Change Recommended" badge was resolved),
  proxy DNS-only. hanvoice.vercel.app remains an alias.
- **Resend: hanvoice.app verified** (eu-west-1, wired via Resend's
  Cloudflare auto-configure). Auth sender is now **hello@hanvoice.app**.
  The API key was REPLACED (`hanvoice-supabase-smtp-v2`, sending-scoped to
  hanvoice.app) because Resend sending keys are domain-scoped and the old
  key could not send from the new domain (Supabase /recover returned 500
  "Error sending recovery email" until the swap). New key lives in
  `backend/.env` as `RESEND_API_KEY` and is pushed into Supabase SMTP.
  **Small cleanup left: revoke the old key** (scoped to
  joshuavanstraaten.com) in the Resend dashboard.
- **Supabase auth**: `site_url` = https://hanvoice.app, allowlist has both
  prod origins + localhost:5173. Live-verified end-to-end: POST /recover →
  mail from hello@hanvoice.app in a real inbox with
  `redirect_to=https://hanvoice.app`.
- **Fly**: `CORS_ORIGINS=https://hanvoice.app,https://hanvoice.vercel.app`
  (both origins preflight-verified), `FRONTEND_URL=https://hanvoice.app`.
- **Paddle: verification SUBMITTED, IN REVIEW** ("We're reviewing your
  details", hanvoice.app shows "In review"; typically a few business days,
  they email; sellers@paddle.com to amend info). Submitted with the
  hanvoice.app URLs (/#pricing, /terms, /privacy, /refunds — all confirmed
  200), trading name "HanVoice", business start 2026-07-05, sole trader,
  compliance answers all "No". **Do NOT create products/prices until the
  Paddle code rewrite** (ROADMAP item 1); the rewrite itself can start
  before approval.
- **PostHog: ACTIVE, verified** — page loads from hanvoice.app POST to
  eu.i.posthog.com and return 200.
- **Sentry: ACTIVE on both stacks, verified** — a thrown test error from
  the live frontend reached project `hanvoice-frontend` (ingest 200 +
  visible in Issues); a `capture_message` fired from inside the Fly machine
  (`flyctl ssh console -C 'python -c …sentry_sdk.init()…'` — init with no
  args reads the SENTRY_DSN env) reached project `hanvoice-api` (message
  "20260712", confirmed in dashboard).

**Nothing in this section blocks build work anymore. Next session =
`HanVoice_Fable5_Goal_Prompt_v1.3.xml`: Paddle billing rewrite + Talk
scenarios (ROADMAP items 1 and 7).**

## What's left

**→ `docs/ROADMAP.md` is the execution order; `docs/BACKLOG.md` is the full
finding list** (Session 1 product/tech audit = items 1–19; Session 2
educational audit = items 20–26; Session 6 GTM asks = items 27–28). Do not
re-audit any dimension — append to BACKLOG, reprioritize in ROADMAP.
**`docs/GTM.md` (session 6) is the marketing contract**: beachhead,
messaging copy, Reddit+TikTok channel plan, 14-day play, NOT-do list —
don't re-litigate channel choice, extend GTM.md instead. ROADMAP
"Immediate" after session 6: items 18–19 (the two GTM copy edits) + item
1's Paddle go-live steps (gated on the approval email). Next session:
`HanVoice_Fable5_Goal_Prompt_v1.5.xml` (content engine).
Analytics and Sentry are live-but-dormant: they activate when Joshua sets
`VITE_POSTHOG_KEY` / `VITE_SENTRY_DSN` in Vercel (+ redeploy) and
`SENTRY_DSN` as a Fly secret.

Session 2 educational verdict worth keeping: Hangul course pedagogy is
strong but teaches only 21 of 40 letters, and lesson 8 uses untaught ones
(커피 ㅋㅍ, 김치 ㅊ, 주세요 ㅔ); money-talk teaches native numbers while the
café scenario answers in sino-Korean; there is zero listening training and
no retention mechanic (judged fatal for the learning mission, High for the
first sale). Minimum viable curriculum is specified at the end of BACKLOG's
Educational section — ~10 content INSERTs, 1 audio-quiz payload variant,
1 simple 1/3/7-day review deck. Content design was specification-only this
session; implementation belongs to v1.3 sessions.

The list below is kept only as original context for items the backlog
references by number.

Audit facts worth keeping: landing page + auth + lesson player + talk loop
all verified working live on a 390×844 viewport, console clean. (The other
session-1 findings — cold start, missing robots/sitemap/OG, raw goal-chip
keys, founder "Get Premium" — are all fixed; see ROADMAP annotations.)

### Original notes (pre-audit)

1. **Stripe (NEXT)** — create products/prices ($69 founder one-time, $14.99/mo
   premium), set the four STRIPE_* env vars as Fly secrets, point the webhook
   at `https://hanvoice-api.fly.dev/api/billing/webhook`. Until then billing
   routes 503 (by design).
2. **Production email** — Supabase's built-in SMTP is rate-limited (~3/hr);
   configure custom SMTP before real signups.
3. **Content depth** — more scenarios (only the café exists; the Talk tab is the
   marquee feature), audio for lesson phrases is generated on demand (could
   pre-generate + cache in Storage), double vowels (ㅐㅔㅘ…) and tense/aspirated
   consonants as Hangul course lessons 9-10, intro explain blocks for the five
   Speak lessons.
4. **Data nit (test account only):** lessons passed *before* the blocks
   migration (café essentials) have a completed `lesson_progress` rollup but no
   `lesson_block_progress` rows, so the player starts them at step 1 unpassed.
   Real users all start post-migration; backfill or ignore.
5. **v2 quality items** — ~~stronger handwriting judge~~ (done session 3:
   `meta/llama-3.2-90b-vision-instruct`), phoneme-level pronunciation
   coaching (needs Azure streaming SDK instead of REST), streaks/gamification,
   romanization toggle as a profile setting, raw-audio persistence for progress
   review (consent + storage), `/api/progress` + `/api/lessons` do N+1 block
   queries per lesson (fine at 13 lessons; batch when content grows), main JS
   chunk is 593 kB gzip 171 kB (build warns; candidate for route-level code
   splitting once it's worth the complexity).

## Learning-experience polish pass (done, 2026-07-05)

Plan: `docs/superpowers/plans/2026-07-05-learning-polish.md` · design:
`docs/superpowers/specs/2026-07-05-learning-polish-design.md`. Three founder
asks from 2026-07-04 evening, all shipped and verified (112 backend / 37
frontend tests green):

- **Audio on every teaching surface.** `chars`/`write`/`example` payloads carry
  an optional `audio` field; a jamo carrier map (frontend `lib/hangulAudio.ts`,
  backend `services/audio_text.py` — keep in sync) resolves bare jamo to a
  spoken carrier syllable (ㄱ → 가, ㅏ → 아, shown as "in 가"). New
  block-scoped audio endpoint `GET /lessons/blocks/{id}/audio?text=…`
  (whitelisted against the block's own payload) + backend in-process LRU
  cache for TTS synthesis (`d875ba3`, `3258a47`). `AudioButton` component
  reused across explain/write/speak blocks. Silence-gate thresholds live in
  `lib/silenceGate.ts` (onset 0.15, silence 0.08, 2.5 s window; cap 4–12 s
  via `recordingCapMs`); silent takes are discarded, never scored.
- **Recording stops itself.** Silence-gate state machine in the recorder
  (`86a4b82`, `61a0c65`) — auto-stops and submits after sustained silence,
  visible state so it's never ambiguous, manual stop still works.
- **Visual identity + motion.** "Hanji" look (Myeongjo display face for Hangul,
  paper texture, motion design tokens — `4d908f7`), skeleton loaders shaped
  like their content instead of spinners (`40ce98c`), step-enter/list-stagger/
  score-ring count-up motion (`d56920f`), and the 도장 (dojang) red-seal stamp
  as the pass celebration (`276b413`).

## Gotchas (hard-won, don't relearn)

- **Resend "Sending access" API keys are scoped to ONE domain.** Changing
  the Supabase SMTP sender to a different domain silently breaks auth mail —
  GoTrue surfaces it as `500 unexpected_failure "Error sending recovery
  email"` on `/auth/v1/recover`, with no mention of SMTP. Diagnose by
  POSTing to api.resend.com/emails with the key directly; fix by minting a
  key scoped to the new domain and re-running `supabase config push`.
- **hanvoice.app DNS lives in Cloudflare but must stay proxy-OFF** (grey
  cloud, "DNS only") on the apex CNAME — the orange proxy in front of
  Vercel breaks cert issuance. Cloudflare flattens the CNAME at apex;
  that's expected.
- **Supabase signs ES256 now:** legacy HS256 secret verifies nothing; backend
  fetches JWKS (`core/security.py`, `199855f`). HS256 kept for tests.
- **NVIDIA's REST API has no speech models** — ASR/TTS are gRPC/Riva only. That's
  why speech is all-Azure (`1005ff4`, `3e5a14f`). Vision judge is
  `meta/llama-3.2-90b-vision-instruct` since session 3 (config default, no
  Fly secret override) — benchmarked against nemotron-nano-vl-8b (zeros
  honest attempts), nemotron-nano-12b-v2-vl and qwen3.5 122b/397b (can't
  separate real writing from scribble). Check `/v1/models` before trying
  another id.
- **Azure short-audio API:** needs `format=detailed` query param; returns scores
  flat on `NBest[0]` (parser accepts both shapes, `5d69701`). Only accepts
  WAV/OGG — browser recordings are converted to 16kHz WAV client-side
  (`26aefcf`, `lib/audio.ts`).
- **VLM handwriting judging is fragile** (`9231a6c`): thin strokes vanish in the
  model's downscale (canvas draws 12px), JSON templates with example `0`s get
  echoed as scores (prompt lists keys without numbers + demands an observation
  sentence first), all-zero results retry once with a nudge.
- **Vite env vars are baked at build**; a module-level throw on missing env got
  the whole app dead-code-eliminated once (`3426705`) — keep env assertions lazy.
- Windows/OneDrive checkout: LF/CRLF git warnings are harmless. Backend venv:
  `backend/.venv/Scripts/python -m pytest|ruff|mypy`. Route order everywhere:
  rate limit → resolve plan → quota → AI call → persist → meter.
- **Run the backend with `PYTHONUTF8=1` on Windows.** structlog prints to the
  console; a log line containing Hangul (e.g. the vision-retry warning quoting
  the target char) crashes the *request* with UnicodeEncodeError on a cp1252
  console. Production containers (UTF-8) are unaffected. Also: port 8000 tends
  to hold a stale uvicorn from an earlier session — probe a new route (404 =
  stale) and kill it before testing new backend code.
- **Never pipe secrets into a CLI from Windows PowerShell 5.1** (`"value" |
  vercel env add …`) — the pipe prepended a UTF-8 BOM (U+FEFF) to every value,
  which Vite baked into the bundle and broke `fetch` with "String contains non
  ISO-8859-1 code point". Write the value to a file with
  `[IO.File]::WriteAllText` (BOM-less) and redirect via `cmd /c "… < file"`.
  Same class of bug: `Get-Content`/`Set-Content` round-trips mangle UTF-8
  files without BOM — use the agent Write/Edit tools for files with Hangul.
  Vercel "Sensitive" env vars pull back as empty strings — inspect the built
  bundle, not `vercel env pull`, when debugging baked values.
- **The PWA service worker serves the stale shell after a redeploy** — the old
  bundle keeps running until the SW updates in the background + next reload.
  When verifying a fresh deploy, unregister the SW / clear CacheStorage first,
  or you'll debug the previous build.
- **Vercel is NOT git-connected** — pushing to GitHub deploys nothing. Deploy
  the frontend with `vercel deploy --prod` from `frontend/` (project is linked
  via `frontend/.vercel/`). Fly deploys via `flyctl deploy --remote-only` from
  `backend/`.
- **Analytics/Sentry are env-gated AND dead-code-eliminated:** with
  `VITE_POSTHOG_KEY` empty at build, Rollup strips posthog-js from the bundle
  entirely (`grep posthog dist/assets/*.js` finds nothing — that's expected,
  not a bug). Setting the key requires a Vercel redeploy to take effect, same
  as every `VITE_*` var. Funnel event names: signup_submitted, signed_in,
  lesson_started, attempt_scored, upgrade_clicked, waitlist_joined
  (`frontend/src/lib/analytics.ts`).
- **`POST /conversations/{id}/turns` takes multipart form-data** (`text` as a
  Form field, `audio` as a file) — JSON bodies get a 422/400. Scripted turns:
  `httpx.post(..., data={"text": "…"})`.
- **Paddle webhook signature format is `ts=…;h1=…`** (semicolon, not comma;
  colon-joined signed payload) — do not confuse with Stripe's `t=…,v1=…`.
  Sandbox and live are entirely separate Paddle accounts with separate
  tokens/prices; `PADDLE_ENV` must match the account the tokens came from.
- Local dev drive recipe (servers, test login, deterministic speak-block pass
  via Azure TTS WAV): `.claude/skills/verify/SKILL.md`.
