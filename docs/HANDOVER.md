# HanVoice — Session Handover

**Date:** 2026-07-04 · **Branch:** `main` · **Status: COMPLETE — all milestones (M1–M10) merged.**

The full application described in `prompt2.xml` and planned in
`docs/superpowers/plans/2026-07-03-hanvoice-full-app.md` is implemented, verified, and
merged to `main` (merge commit `a4acfde`). Verification at merge time: backend
`ruff check .` + `mypy app` (strict) clean, **79 tests passing**; frontend `eslint` +
`tsc` clean, **12 tests passing**, production PWA build green; both Docker images
built and smoke-tested (backend `/api/health` ok; nginx SPA fallback + service-worker
no-cache confirmed).

## Where things live

- **What/why/how:** `README.md`, `docs/architecture.md`, `docs/api.md`,
  `docs/deployment.md`, `docs/schema.md`
- **Source of truth artifacts:** `supabase/migrations/` (schema + usage RPC),
  `prompts/scenarios/cafe_iced_americano_v1.md` (barista contract), the plan doc
- **Commands:** backend `cd backend && ./.venv/Scripts/python -m pytest|ruff|mypy`;
  frontend `cd frontend && npm run lint|typecheck|test|build`

## Not done (deliberate v1 scope — revisit when needed)

- No raw audio/image persistence (analyze-and-discard)
- No Redis (in-process rate limit; Postgres daily quota is the cross-instance authority)
- No remote/CI has ever run — the repo has **no git remote**; push to GitHub to
  activate `.github/workflows/ci.yml`
- Not deployed; follow `docs/deployment.md` (Supabase project + container host +
  static host, Stripe webhook)

## Live environment (2026-07-04)

Supabase project **hanvoice** (`mxibibkcaarltsbkomvm`, eu-west-1, free tier) is
migrated + seeded; `frontend/.env` and `backend/.env` are wired (gitignored).
Test account: `joshuavanstraaten100+hanvoice-test@gmail.com` (confirmed via SQL).
Azure Speech key live (northeurope, F0) — pronunciation + TTS. NVIDIA key live —
Llama conversation verified in-browser (goals, corrections, audio all working).
Stripe still unset. **TTS moved to Azure** (`1005ff4`): NVIDIA Magpie is
gRPC-only, no REST — don't switch back without a Riva client.

## Gotchas worth remembering

- **Supabase signs ES256 now:** new projects issue asymmetric tokens with a `kid`;
  the legacy HS256 secret verifies nothing. Backend resolves keys from the JWKS
  endpoint (`core/security.py`, fix `199855f`) with HS256 kept for tests.
- **VLM handwriting judging is fragile** (`9231a6c`): thin strokes become
  invisible after the model's downscale (canvas draws 12px now); JSON templates
  with example `0` values get echoed as scores (prompt lists keys without
  numbers, demands an observation sentence first); all-zero results retry once.
  The 8B judge's jamo precision is coarse — v2 candidate: stronger vision model.
- Test account holds a manually-granted founder pass (200/day quotas) for testing.

- **Vite env DCE:** `import.meta.env.VITE_*` is statically replaced at build; a
  module-level throw on missing env made Rollup eliminate the entire app from the
  bundle (fixed by lazy-initializing the Supabase client — see commit `3426705`).
  Keep top-level env assertions out of frontend modules.
- Windows/OneDrive checkout: git prints LF/CRLF warnings — harmless.
- stripe v15: `event.data.object.to_dict()` (StripeObject is no longer a dict).
- respx tests: mock every Supabase table a request touches or you get 500s.
- Route order everywhere: rate limit → resolve plan → quota → AI call → persist →
  meter (quota errors must cost nothing).
