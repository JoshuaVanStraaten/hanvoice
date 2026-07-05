# API reference

Base path: `/api`. Interactive docs live at `/docs` (FastAPI/OpenAPI) when the
backend is running.

**Auth:** all endpoints except `/health`, `/waitlist`, and `/billing/webhook` require
`Authorization: Bearer <supabase access token>`.

**Errors:** every error is `{"error": {"code": "...", "message": "..."}}`. Notable
codes: `quota_exceeded` (429 — daily limit hit, no AI spend occurred),
`rate_limited` (429), `ai_service_unavailable` (503), upstream failure (502).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness — `{"status": "ok"}` |
| GET | `/me` | Profile + resolved plan + founder flag |
| PATCH | `/me` | Update `display_name` / `native_language` |
| GET | `/usage/today` | Today's counters + plan limits |
| GET | `/lessons` | Lesson summaries (with block counts) |
| GET | `/lessons/{slug}` | Lesson with ordered blocks + per-block pass state |
| POST | `/lessons/blocks/{id}/complete` | Mark an explain/quiz block passed (speak/write pass only via scored attempts) |
| GET | `/lessons/blocks/{id}/audio` | Teaching audio for a glyph on this block (`?text=` must be one of the block's authored sounds; bare jamo speak their carrier syllable, e.g. ㄱ → 가). Cached, rate-limited, unmetered |
| GET | `/pronunciation/phrases/{id}/audio` | Reference TTS for a phrase (base64 mp3). Cached, rate-limited, unmetered |
| GET | `/scenarios` | Conversation scenarios + completion goals |
| POST | `/pronunciation/attempts` | Multipart `audio` + `phrase_id` (or `target_text`) → Azure scores + per-word detail |
| POST | `/conversations` | JSON `{scenario_slug}` → session + Minji's opener + TTS audio (base64) |
| POST | `/conversations/{id}/turns` | Multipart `audio` *or* `text` → user + assistant messages, goals, TTS |
| POST | `/conversations/{id}/complete` | Mark the session completed |
| GET | `/conversations/{id}` | Session + full message history |
| POST | `/handwriting/attempts` | JSON `{target_text, image_base64, block_id?}` (PNG ≤ 2 MB) → vision scores + feedback; with `block_id`, a pass (≥ 60) marks the block |
| GET | `/progress` | Lesson + scenario rollups |
| POST | `/waitlist` | Anonymous `{email, source?}` → 201 (duplicate-safe) |
| POST | `/billing/checkout` | `{plan: "premium"|"founder"}` → Stripe checkout URL (503 if Stripe unconfigured) |
| POST | `/billing/webhook` | Stripe events (signature-verified) → subscriptions / founder passes |

## Metered endpoints

`/pronunciation/attempts`, `/conversations/{id}/turns`, and `/handwriting/attempts`
are quota-gated per plan and rate-limited per user. The quota check runs before the
AI call: a 429 costs nothing. Limits come from the `plans` table (see
[schema.md](schema.md)).

## Media constraints

- Audio: `audio/webm`, `audio/wav`, `audio/ogg`, `audio/mpeg`, `audio/mp4`, ≤ 10 MB
  (~30 s). The web client records webm/opus (mp4 on Safari).
- Handwriting: base64 PNG (no `data:` prefix), ≤ 2 MB, target text ≤ 40 chars.
- Audio and images are analyzed and discarded — never persisted in v1.
