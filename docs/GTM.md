# HanVoice Go-to-Market — the first paying customer

**Created:** 2026-07-12 (Session 6, `HanVoice_Fable5_Goal_Prompt_v1.4.xml`).
**Mission:** ONE person pays $69 for a founder pass. Not a growth machine.
**Budget:** ~5 h/week founder time, ~$0 cash.
**Hard constraint:** Paddle is sandbox-only until the approval email arrives —
the money-ask is sequenced *after* approval; everything before it is audience
work that needs no billing.

Every line below was tested against: *does this find one person who pays?*

---

## 1. Positioning

One sentence per segment, then the pick.

| Segment | Positioning sentence | Honest today? |
|---|---|---|
| **Korea-trip-booked beginner** | "Land in Seoul able to order coffee, take a taxi, and shop the market — out loud, and understood." | **Yes.** The 5 scenarios ARE the trip. ~5 h of content is *right-sized* for trip prep, not a wall. |
| K-drama/K-pop fan | "Stop mouthing along to lyrics — learn to actually say it, with an AI that scores your pronunciation." | Partly. They want a long road to fluency; we have no listening training or retention mechanic yet. They'd hit the content wall in a weekend and churn loudly. |
| Complete beginner (no deadline) | "The Korean app that makes you speak from lesson one — not tap flashcards." | Partly. Same content-wall problem; no urgency to convert. |
| Expat in Korea | "Survive real Korean counters — café, taxi, market — with pronunciation feedback before you embarrass yourself." | Mostly, but they're few, scattered, and often past our beginner content. |
| Afraid-to-speak learner | "Practice speaking Korean where nobody can laugh — an AI partner with infinite patience." | Yes as an *angle*, but it's a psychographic, not a findable audience. Use it as messaging inside other segments. |

### Beachhead: the Korea-trip-booked beginner

Defence, in order of weight:

1. **Product-truth fit is exact.** What's live is Hangul reading + 36 phrases +
   pronunciation scoring + AI roleplay of café/restaurant/taxi/market/first-meeting.
   That is a trip-prep product. No promise-stretching needed — the known gaps
   (21/40 letters, no listening drills, no review deck) don't break a 2-week
   trip-prep use case the way they break a "become conversational" promise.
2. **Deadline = conversion pressure.** A flight date is a natural forcing
   function. K-pop fans can defer forever; a traveler flying in 6 weeks cannot.
3. **Money is already out.** Someone spending $1,500+ on a Korea trip treats
   $69 as trip insurance ("don't be the tourist pointing at menus"). A one-time
   founder pass fits a one-time event far better than a subscription pitch.
4. **Findable with zero budget.** r/koreatravel (~400k+), Korea-travel TikTok,
   travel-planning threads — high intent, concentrated, free to reach.

The K-content fan is the *scale* segment for later — after the Next Month
retention/listening work makes the long-journey promise honest.

---

## 2. Messaging (landing page)

- **Headline:** *Speak Korean before you land in Seoul.*
- **Subhead:** *Learn to read Hangul and say the phrases your trip actually
  needs — with real pronunciation scoring and an AI you can rehearse café,
  taxi, and market conversations with, out loud.*
- **Proof points (3):**
  1. **Your pronunciation, actually scored.** Every phrase you speak gets a
     0–100 score from professional speech assessment — you know you're
     understandable *before* you need to be.
  2. **Rehearse the real situations.** Order at a café, take a taxi, haggle at
     a market, introduce yourself — with an AI partner who stays in character
     and tracks whether you got what you asked for.
  3. **Start reading Hangul in a weekend.** Guided lessons with handwriting
     checks turn menus and signs from noise into words.

Honesty lines we do NOT cross (per the educational audit): no "become fluent",
no "complete Hangul course" (21 of 40 letters today), no "train your ear"
(zero listening drills), no "never forget" (no review mechanic). "Trip-ready
phrases + pronunciation confidence" is fully true today.

Product change required (landing headline/subhead/proof-point copy swap) →
**BACKLOG item 27 / ROADMAP Immediate item 18**. It's a copy edit, not a
rebuild — Session 1's "don't rebuild the landing page" verdict stands.

---

## 3. Channel plan

Evaluation against: founder is one person, 5 h/week, South Africa timezone,
already runs a YouTube-Shorts content pipeline for another venture (editing
skills + tooling exist).

| Channel | Verdict | Reasoning |
|---|---|---|
| **Reddit** | **DO — primary** | Highest intent per minute spent. r/koreatravel is literally people planning the trip; r/Korean and r/languagelearning allow honest builder/feedback posts. Text-only = cheapest content. Risk: self-promo rules — mitigate by being a genuine participant first, links only where rules allow. |
| **TikTok** | **DO — secondary** | The differentiator is *audible* — a screen recording of Minji conversation + live pronunciation score is a native TikTok demo. Korea-travel prep content thrives there. Founder already has a shorts pipeline. 2 videos/week max. |
| YouTube Shorts | Free rider only | Cross-post the TikToks unedited (pipeline already exists). Zero extra effort allowed; no separate strategy, no channel-building work. |
| Instagram | **SKIP** | Reels would be the same videos, but IG demands feed aesthetics + story cadence to convert. Third platform to babysit; adds reach, not intent. |
| X | **SKIP** | No dense Korean-learner or Korea-travel audience; buildinpublic X is founders selling to founders. Zero path to customer #1. |
| Discord | **SKIP** | Learning servers ban promotion hard, and presence-building is the most hours-hungry channel there is. Incompatible with 5 h/week. |
| SEO | **SKIP (as a project)** | Payback is 3–6 months; we need one customer in weeks. The session-5 surface (OG/robots/sitemap) is enough. No blog engine. |

**The two channels: Reddit (primary) + TikTok (secondary), with TikToks
cross-posted to YouTube Shorts for free.** Weekly budget: Reddit ~2 h,
TikTok ~2.5 h (2 videos), email ~30 min.

---

## 4. Email capture + referral loop

**Capture (near-zero build):** the landing waitlist form already posts to a
real `/waitlist` endpoint. Upgrade the *offer*, not the plumbing: "Get the
free **Seoul Survival Phrase Card** (the 36 phrases with pronunciation tips)
+ founder-launch discount." The phrase card is a one-page PDF assembled from
existing lesson content — founder makes it once on Day 1. Delivery is manual
via Resend at this scale (a broadcast every few days beats building
automation for 20 subscribers). Copy change → **BACKLOG item 28 / ROADMAP
Immediate item 19**.

**Referral (zero build):** after go-live, every founder-pass purchase gets a
personal thank-you email containing a Paddle **discount code** ($10 off) "for
one friend also going to Korea." Paddle discount codes are a dashboard
feature — no code, no schema, no engineering. If ≥3 referred purchases ever
happen, *then* consider building anything.

Explicitly not building: in-app referral links, credit ledgers, share
buttons. All engineering for users we don't have.

---

## 5. The first-customer play — 14 days

Assumes ~40 min/day. The money-ask is **gated on the Paddle approval email**,
not on a calendar day — days 1–11 are deliberately billing-free audience
work. Go-live itself is ~1 h (click-by-click already in HANDOVER.md).

**Day 0 (prep, before the clock starts):** verify the funnel end-to-end with
a fresh signup (PostHog events firing, auth mail arriving from
hello@hanvoice.app). Ship the two copy changes (items 18–19) — they're the
only build work in this plan.

- **Day 1 — Assets.** Make the Seoul Survival Phrase Card PDF from existing
  lesson phrases. Create the TikTok account (@hanvoice or similar). Reddit:
  use the founder's real account — brand accounts get flagged.
- **Day 2 — Reddit recon.** Read the top month of r/koreatravel, r/Korean,
  r/languagelearning; write down each sub's self-promo rules. Helpfully
  answer 2 phrase/pronunciation questions. No links, no mention of the app.
- **Day 3 — TikTok #1.** Screen + voice demo: "POV: ordering an iced
  americano in Korean and the app grades your pronunciation live." Show a
  real score. Cross-post to YT Shorts.
- **Day 4 — Reddit value post.** r/koreatravel: "The 12 Korean phrases that
  actually got used, from someone who built a speaking app around them" —
  full value in the post body; app mention only where rules permit (usually
  a comment when asked).
- **Day 5 — TikTok #2.** Taxi scenario ("saying 명동까지 가 주세요 until the
  AI understood me"). Reply to every comment on #1.
- **Day 6 — Email #1 to waitlist.** Deliver the phrase card. One question:
  "When's your trip?" Every reply is a warm lead with a date.
- **Day 7 — Review (30 min).** PostHog: visits → signups by source. Whichever
  video/post drove signups defines next week's content. Kill what didn't.
- **Day 8 — TikTok #3.** Challenge format: "Can you beat 80/100 saying
  주세요? My pronunciation scorer says most people can't." Invite duets.
- **Day 9 — Reddit builder post.** r/Korean or r/languagelearning (whichever
  rules allow): "I built a speaking-first Korean app — brutal feedback
  wanted." Feedback framing is allowed almost everywhere, is honest, and
  converts better than ads. Answer everything, fast.
- **Day 10 — DM day.** Personal reply to every commenter, waitlist reply,
  and feedback-giver. Ask trip dates. Goal: 5 named warm leads.
- **Day 11 — TikTok #4** (best-performing format repeated). Draft the launch
  email.
- **Day 12 — GO LIVE + the ask** *(if Paddle approval has arrived)*. Run the
  HANDOVER go-live steps (~1 h), verify with the documented self-purchase
  smoke. Then the launch email to the waitlist: founder pass, $69 one-time,
  explicitly capped/first-supporters framing, direct link to checkout.
- **Day 13 — Personal asks.** Individual messages to the 5 warmest leads —
  short, plain, founder voice: "You said you fly in March — founder pass is
  live, $69 once, here's the link. Any question, just reply." Post a "we're
  live" update on the Day-9 feedback thread and a launch TikTok.
- **Day 14 — Last call + tally.** Follow-up email answering the objections
  heard during the week. Count: visitors, signups, replies, purchases.
  Whatever the number, write down *why* people didn't buy — that's Session
  v1.5's input.

**Paddle contingency (likely, per approval timelines):** if the approval
email hasn't arrived by Day 11, days 12–14 run unchanged except the ask
becomes a **reservation**: "Founder pass is $69, first N people — reply
'mine' to lock it at launch." The launch email then fires the same day the
approval lands, to reservers first. The 14-day play never stalls on Paddle;
it just decouples *ask* from *charge*.

**Definition of success:** one completed Paddle transaction from a stranger
(not the test account, not a friend). Secondary: ≥25 waitlist emails and ≥5
warm leads with trip dates — that's a repeatable pipeline even if day 14
closes at zero.

---

## 6. NOT-do list

- **No paid ads** — Meta/TikTok/Google. $0 budget, and ads amplify a funnel
  we haven't proven converts.
- **No Instagram, X, or Discord presence.** Decided above; revisit only after
  customer #1.
- **No SEO/blog content engine.** Wrong timescale for this mission.
- **No Product Hunt launch.** Audience is founders and makers, not
  Korea-bound travelers; it's a one-shot dopamine hit that burns a week.
- **No influencer outreach campaigns.** Cold-emailing K-content creators from
  a zero-follower account is spam; revisit with traction proof.
- **No referral engineering, no email automation, no CMS** — manual
  everything until volume forces the issue.
- **No new features for marketing's sake.** The two copy items (18–19) are
  the entire build budget. The Next Month roadmap (retention, listening,
  complete Hangul) proceeds on its own track and is NOT a launch dependency.
- **No discounting below $69** and no "free founder passes for feedback" —
  feedback we get anyway; a discounted first customer proves nothing.
- **No K-pop fan campaign yet.** It's the bigger market and the wrong first
  target; it becomes primary after retention + listening ship (Next Month),
  which is exactly when its promise becomes honest.

---

## Hand-off to v1.5 (content engine)

The channel plan v1.5 must execute: **Reddit primary + TikTok secondary**,
beachhead = trip-booked beginner, formats proven/killed by the Day-7 and
Day-14 reviews. Inputs it will need from this play: PostHog source data,
which video format won, the objection list from Day 14.
