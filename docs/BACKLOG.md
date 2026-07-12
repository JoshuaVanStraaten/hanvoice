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

## Educational — Session 2 audit, 2026-07-12: can it teach conversational Korean?

Judged as a Korean-language educator against the make-or-break question:
*can a complete beginner reach basic conversational ability?* Verdict:
**the Hangul course (lessons 1–8) is genuinely good pedagogy** — mouth-shape
mnemonics, do-to-pass gating, correct ordering through syllable building,
batchim, and sound change — and the café prompt is well-designed scene work
(beat structure, in-character corrections, one question per turn). But today
the app teaches a learner to *read most Hangul* and *pronounce 36 phrases*.
It does not yet build listening, recall, or enough language to hold any
conversation beyond the café script. Findings, severity = distance from a
learner reaching conversation (and staying subscribed):

20. **The Hangul course teaches 21 of 40 letters — and lesson 8 uses letters
    it never taught.** (High) Missing entirely: aspirated ㅋㅌㅍㅊ, tense
    ㄲㄸㅃㅆㅉ, compound vowels ㅐㅔㅒㅖㅘㅙㅚㅝㅞㅟㅢ. Concretely broken
    sequencing: lesson 8 has learners read/speak 커피 (ㅋ, ㅍ), 김치 (ㅊ),
    and 주세요 (ㅔ) — none taught. Learners also can't read 네, 얼마예요,
    뭐예요, 반가워요 from the Speak lessons. Fix is content-only: 2 new
    lessons (aspirated+tense; compound vowels) inserted *before*
    `read-and-say-it`. (Extends HANDOVER item 3.)
21. **Content wall at day 2–3.** (High) ~3–4 h of Hangul course + 25 speak
    phrases (~1 h) + one 5-minute scenario. A motivated beginner exhausts
    everything in a weekend, well short of conversational ability — then has
    nothing to subscribe *to*. $69 lifetime buys ~5 h of content. Vocabulary
    is ~60–70 unique words vs ~300 for survival-level conversation.
22. **No retention mechanic — judged: fatal for the mission, High for the
    first sale.** Nothing resurfaces learned material (no review, SRS,
    streak, or reminder). Speech requires *recall*, and single-exposure
    recall decays in days — so "HanVoice takes you to conversation" is not
    honest without review. The first $69 sale can still ride day-1/2
    enthusiasm, which is why this is High not Critical. Minimum fix, not an
    SRS engine: a daily review deck of already-passed phrases on fixed 1/3/7
    day intervals + a visible streak.
23. **Zero listening comprehension training.** (Medium-High) Every mechanic
    scores *production*; nothing trains parsing Korean by ear — yet Talk
    requires understanding Minji at speed, and her English translation is
    always on screen, so users read instead of listen. Cheap fix within the
    existing block system: quiz blocks with an audio prompt (hear → choose
    meaning), and a "hide translation" toggle in Talk.
24. **Number-system mismatch breaks the money loop.** (Medium) `money-talk`
    teaches native numbers 하나 둘 셋; prices in Korea (and in the café
    scenario: 사천오백 원) use sino-Korean numbers, which are taught
    nowhere. The learner is taught to ask 얼마예요? but cannot understand
    any answer to it. Fix: a sino-numbers/prices micro-lesson; native
    numbers can wait.
25. **Speak lessons are bare phrase lists with no scaffolding.** (Medium)
    No intro explain blocks (HANDOVER item 3), and no pattern extraction:
    주세요 appears in 6 phrases across 4 lessons and is never called out as
    "NOUN + 주세요 = please give me NOUN"; 이에요/예요 and 네/아니요 are
    never taught at all. One explain block per Speak lesson + 2–3 pattern
    micro-lessons converts memorized strings into generative language.
26. **Lesson→scenario loop is broken.** (Medium, pairs with item 9)
    restaurant-basics, getting-around, and money-talk teach phrases with no
    scenario to use them in — the practice feature that would cement them
    (and justify paying) doesn't exist for 4 of 5 Speak lessons. Scenario
    per existing lesson first; new topics second.

**Minimum path to "basic conversational ability"** (specification, not
feature wishlist — everything is INSERTs + two small mechanics):
complete Hangul (2 lessons) → sino-numbers + 이에요/예요 + 주세요-pattern
micro-lessons (3 lessons) → intro blocks on Speak lessons → 4 scenarios
matching existing Speak lessons → audio-quiz listening blocks → 1/3/7-day
review deck + streak. Roughly: ~10 content INSERTs, 1 new quiz payload
variant, 1 review mechanic. That is the whole gap between "Hangul app" and
"conversation app".

## What's already good (don't fix what isn't broken)

Marketing landing page exists and is strong (hero, demo phrase, 3 features,
pricing, waitlist capture — waitlist posts to a real `/waitlist` endpoint);
auth round-trip, lesson stepper with resume, teaching audio, conversation
loop with live goal tracking, romanization + translation, graceful 404, and
labeled/accessible controls throughout all verified working live. Console was
clean across the whole session except the expected billing 503.
