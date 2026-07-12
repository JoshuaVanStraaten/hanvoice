# HanVoice Content Engine — a week of content in one sitting

**Created:** 2026-07-12 (Session 7, `HanVoice_Fable5_Goal_Prompt_v1.5.xml`).
**Serves:** `docs/GTM.md` — beachhead = Korea-trip-booked beginner; channels =
Reddit (primary) + TikTok (secondary), TikToks cross-posted to YouTube Shorts
unedited. Channel choice is settled; this doc only says how to feed it.
**Budget:** ~5 h/week, of which one ~3 h batch sitting produces everything.
**Ready-to-post batch #1:** `docs/content/week-01/` (3 TikTok scripts, 1 Reddit
post, 1 waitlist email, + the Seoul Survival Phrase Card).

Every template below is copy-paste complete: paste into any LLM chat, fill the
`{PLACEHOLDERS}`, and the output is a draft you edit for voice — never post raw
AI output on Reddit; it gets sniffed and nuked.

---

## 0. Formats: chosen and killed

| Format | Verdict | Why |
|---|---|---|
| **Tourist-phrase demo (TikTok)** | **KEEP — flagship** | The differentiator is audible: real phrase, live pronunciation score on screen. Native demo, zero acting skill needed. |
| **Pronunciation tip / challenge (TikTok)** | **KEEP** | "Can you beat 78/100 saying 주세요?" invites duets and comments; tips ("the ㅈ in 주세요 isn't J") show teaching credibility. |
| **Common mistakes / trip value (Reddit text)** | **KEEP** | r/koreatravel rewards dense, honest, listicle-free value posts. Cheapest format per minute; highest intent per view. |
| K-drama phrase breakdowns | **KILL** | Wrong segment until retention + listening ship (GTM §1) — attracts the fan audience we explicitly deferred. |
| K-pop lyric explanations | **KILL** | Same reason, worse: lyric Korean is non-survival Korean; zero trip-prep overlap. |
| Korean slang | **KILL** | Fun, viral-ish, but attracts learners with no deadline — the segment GTM rejected. |
| Daily Korean (word-of-day) | **KILL** | Commodity format owned by big accounts; no differentiation, no urgency, daily cadence breaks the 5 h budget. |

Rule of thumb for any future format idea: *would someone flying to Seoul in 6
weeks save this?* If not, it's for a segment we're not serving yet.

---

## 1. Format A — Tourist-phrase demo (TikTok, cross-post YT Shorts)

**What it is:** 20–40 s screen + voice recording. You say a real trip phrase
into HanVoice, the score appears live, optionally Minji replies in a scenario.
The product IS the content.

### Production steps (~50 min/video, drops to ~35 with practice)

1. **Script** (10 min): run the script prompt below, edit for voice.
2. **Record** (15 min): phone screen-record hanvoice.app (logged in, phone in
   Do Not Disturb). 2–3 takes of the phrase in the lesson or Talk scenario.
   An imperfect score (70–85) is BETTER content than 95 — it's believable and
   shows the app catching real mistakes.
3. **Edit** (15 min): existing shorts pipeline (CapCut). Hook text on screen
   in the first second. Captions burned in (most viewers on mute). Trim dead
   air hard.
4. **Post** (10 min): TikTok with caption + 3–5 hashtags, then upload the same
   file to YT Shorts unedited. Reply to comments same day.

### Script prompt template (paste into an LLM)

```
You write 25–40 second TikTok scripts for HanVoice (hanvoice.app), an app for
people flying to Korea soon. It teaches Hangul reading + trip phrases with
real pronunciation scoring (0–100) and AI conversation rehearsal (café, taxi,
restaurant, market, first meeting). NEVER claim: fluency, a complete Hangul
course, or listening training. Tone: first-person builder/learner, casual,
no cringe, no "hey guys".

Write a script for this phrase demo:
- Phrase: {HANGUL} ({ROMANIZED}) — "{ENGLISH}"
- Situation it saves you in: {SITUATION, e.g. "ordering at a Seoul café"}
- My real score on camera: {SCORE}/100

Format the output as:
HOOK (on-screen text + first spoken line, must work in 1 second)
BEAT-BY-BEAT (what I show + say, one line per beat, max 6 beats)
CTA (spoken, one line — send viewers to the free Seoul Survival Phrase Card
at the link in bio; never mention pricing)
CAPTION (1–2 sentences + 4 hashtags mixing #koreatravel #learnkorean and one
phrase-specific tag)
Give 3 alternative hooks at the end.
```

### Hook variants (proven shapes, rotate)

- POV: "POV: it's your first morning in Seoul and you actually order in Korean"
- Fear: "Don't be the tourist pointing at the menu"
- Challenge: "The app said my Korean was 74/100. Rude. Accurate, but rude."
- Countdown: "Flying to Korea in 6 weeks? Learn this one first."
- Result: "This is the exact phrase that got me my coffee in Myeongdong"

**Visuals:** none generated — the screen recording is the visual. No GPT
Image / Nano Banana in this format.

---

## 2. Format B — Pronunciation tip / challenge (TikTok, cross-post YT Shorts)

**What it is:** 15–30 s. One concrete pronunciation trap + the fix, proven on
screen with a score. Challenge variant: show your score, dare viewers to beat
it, invite duets.

### Production steps (~40 min/video)

Same pipeline as Format A; recording is shorter (one phrase, two takes: the
"wrong" way and the fixed way — the score difference is the story).

### Script prompt template

```
You write 15–30 second TikTok scripts about Korean pronunciation for
beginners flying to Korea. The app on screen is HanVoice (hanvoice.app):
real 0–100 pronunciation scoring. Tone: specific, slightly cheeky, zero
academic jargon (no "aspirated consonant" — say "the puff of air").

Write a script about this trap:
- Phrase: {HANGUL} ({ROMANIZED}) — "{ENGLISH}"
- The mistake English speakers make: {MISTAKE, e.g. "saying JU-SAY-YO like English J"}
- The fix in mouth-feel terms: {FIX, e.g. "softer, between J and CH, no puff"}
- My before/after scores: {LOW}/100 → {HIGH}/100

Output: HOOK, BEAT-BY-BEAT (max 5 beats, must include both scores on screen),
CTA (free Seoul Survival Phrase Card, link in bio), CAPTION + 4 hashtags,
3 alternative hooks. For a CHALLENGE variant, end the script daring viewers
to duet with their attempt.
```

**Visuals:** screen recording only. Optional cover frame if a video needs a
thumbnail; image prompt template:

```
Generate a 9:16 cover image: bold hangul "{HANGUL}" centered on a warm
paper-textured background (off-white #F6F4EF), a red-to-jade score ring
graphic showing {SCORE}, large sans-serif English text "{HOOK_TEXT}" at the
top third. Clean, flat, no photorealism, no watermark, no extra text.
```

---

## 3. Format C — Trip-value / common-mistakes post (Reddit)

**What it is:** a long-form text post for r/koreatravel (also r/Korean,
r/languagelearning where rules allow) that is 100% useful without clicking
anything. The app appears only where sub rules permit — usually as a comment
reply when asked, or a single non-pushy mention. **Trust is the asset;
one spammy post burns the account.**

### Production steps (~45 min/post + ~15 min/day engagement)

1. **Draft** (20 min): run the prompt below, then REWRITE in your own voice —
   Reddit detects AI prose. Typos are fine; marketing polish is fatal.
2. **Rules check** (5 min): reread the target sub's self-promo rules that day.
3. **Post + first hour** (20 min): post at 14:00–16:00 SAST (US morning).
   Answer every comment in the first hour — early replies decide reach.
4. **Daily engagement** (15 min/day, from the weekly budget): answer
   phrase/pronunciation questions across the three subs, no links unless asked.

### Post prompt template

```
You draft Reddit posts for r/koreatravel. Author persona: a solo developer
who built a Korean speaking-practice app (HanVoice) and actually studies the
phrases himself. The post must be 100% valuable with zero links — the app is
mentioned at most once, casually, as context ("I built a little app to drill
these"), never as a pitch. NEVER invent Korean: use only the phrases I
provide. NEVER claim fluency or a complete course.

Topic: {TOPIC, e.g. "the phrases that actually got used on a 10-day trip" or
"5 mistakes English speakers make ordering in Korean"}
Phrases to draw from (hangul / romanized / english):
{PASTE PHRASES FROM docs/content/week-01/seoul-survival-phrase-card.md}

Output: 3 title options (specific, no clickbait), then the post body —
conversational, concrete situations, phrase + how to actually say it +
what the reply will sound like. 350–600 words. End with a genuine question
to the sub, not a CTA.
```

**Visuals:** none. Text is the format.

---

## 4. Weekly schedule (~5 h, one batch sitting + daily crumbs)

| When | What | Time |
|---|---|---|
| **Sunday batch sitting** | Generate + edit 2 TikTok scripts and 1 Reddit draft (templates above), record + edit both videos, draft the waitlist email if one is due | ~3 h |
| Tue | Post TikTok #1 + YT Short, reply to comments | 15 min |
| Thu | Post TikTok #2 + YT Short, reply to comments | 15 min |
| Wed | Post the Reddit piece (14:00–16:00 SAST), babysit first hour | 30 min |
| Daily (Mon–Fri) | Reddit engagement: answer 1–2 questions, no links | 10–15 min |
| Fri | Waitlist email (when due — every ~2 weeks) via Resend broadcast | 20 min |
| **Sunday, before the batch** | KPI review ritual (§6) | 15 min |

Cadence floor: 2 TikToks + 1 Reddit post per week. If a week collapses, drop
the Reddit post, keep the TikToks — the account's consistency signal matters
more on TikTok; Reddit forgives absence.

---

## 5. CTA + funnel — what must exist at each step

Every piece of content carries ONE ask, and until the Paddle approval email
arrives, that ask is never a purchase.

| Step | Mechanism | Status |
|---|---|---|
| Post → profile | TikTok bio link + Reddit profile/comment mention → `https://hanvoice.app` | ⚠ Founder Day-1 task (GTM §5): create the TikTok account, set the bio link. No build. |
| Profile → landing | hanvoice.app with GTM §2 trip-prep copy | ✅ Shipped this session (ROADMAP 18). |
| Landing → email | Waitlist form offering the **Seoul Survival Phrase Card** + launch discount | ✅ Shipped this session (ROADMAP 19). Form posts to the real `/waitlist` endpoint; `waitlist_joined` fires in PostHog. |
| Email delivery | Manual Resend broadcast sending the card | ⚠ Founder manual step; card asset exists (`docs/content/week-01/seoul-survival-phrase-card.html` — print to PDF once, attach/link forever). |
| Email → signup | Card email includes "practice these out loud" link → `/signup` | ✅ Auth live, mail from hello@hanvoice.app verified. |
| Signup → founder pass | **Until Paddle approval:** reservation ask only (GTM §5 contingency — "reply 'mine' to lock $69 at launch"). **After approval email:** live checkout link. | ⚠ Gated on Paddle. Go-live steps in HANDOVER.md. |

**Nothing new for ROADMAP Immediate** — the two build items (18–19) shipped
this session; every remaining ⚠ is a founder action already sequenced in the
GTM 14-day play, not engineering.

Hard rules for every CTA, in every format, until further notice:
- Product truth only: 13 lessons (8 Hangul + 5 Speak), 5 Talk scenarios,
  pronunciation scoring, handwriting checks. Never "complete Hangul" (21/40
  letters), never "train your ear", never "never forget".
- The public ask is always the free phrase card, not money. Money asks live
  in email, to people who opted in, per the GTM sequencing.

---

## 6. Metrics + the 15-minute Sunday review

Vanity (ignore): follower counts, likes, total views across all videos.

The funnel numbers that matter, in order:

1. **Landing visits by source** (PostHog: referrer/UTM) — did the week's
   content move anyone at all?
2. **Waitlist joins** (`waitlist_joined`) and **signups** (`signup_submitted`)
   per source — the only proof a format works.
3. **Per-piece signal:** for each TikTok, profile-link taps proxy =
   that day's landing visits; for Reddit, upvote ratio + comment quality.
4. **Warm leads:** replies to waitlist emails with a trip date (kept in a
   plain list — no CRM).

Ritual (15 min, Sundays, before the batch sitting):
- Open PostHog → last 7 days → visits by source, waitlist joins, signups.
- One decision per format: **double down / tweak hook / kill.** A format gets
  3 weeks of tries before a kill verdict; a single video gets none (one flop
  means nothing).
- Write one line in a running log at the bottom of this file: date, numbers,
  the decision. That log is the input for the next strategy session.

## Review log

| Date | Visits (by source) | Waitlist | Signups | Decision |
|---|---|---|---|---|
| _(first entry after week 1)_ | | | | |
