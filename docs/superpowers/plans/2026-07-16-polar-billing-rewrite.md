# Polar billing rewrite (Paddle → Polar)

**Date:** 2026-07-16 · **Status:** IN PROGRESS
**Why:** Paddle rejected the account twice (AI-assessment AUP). Polar account
is live and approved (same-day KYC). Decision + rationale:
`_os/DECISIONS.md` 2026-07-16. Account/products/webhook already exist —
ids in `backend/.env` (`POLAR_*`).

## Architecture (delta from Paddle)

Paddle: backend served overlay *config*; client opened Paddle.js overlay;
`custom_data` was client-influenced, so webhook cross-checked price ids.

Polar: backend **creates the checkout session server-side**
(`POST https://api.polar.sh/v1/checkouts/` with org access token) and
returns `{url}`; frontend redirects (`window.location.assign`). `metadata`
(`user_id`, `plan`) is server-set → trusted, but webhook still cross-checks
`product_id` (defense in depth). No Polar JS SDK; no client token; the
`@paddle/paddle-js` dependency is deleted.

Webhook = standard-webhooks spec, NOT Paddle's `ts;h1`:
- Headers: `webhook-id`, `webhook-timestamp`, `webhook-signature`
  (format `v1,<base64 hmac>`, may be space-separated list).
- Signed content: `{id}.{timestamp}.{raw_body}`, HMAC-SHA256.
- **Key ambiguity:** Polar docs say "base64-encode your configured secret"
  (key = literal secret string incl. `whsec_`); standard-webhooks spec says
  key = base64-decode of the part after `whsec_`. Verify against BOTH
  candidate keys; accept if either matches. Tolerance 5 min.
- Events subscribed (endpoint be4a23aa…): order.paid, order.refunded,
  subscription.{created,updated,active,canceled,uncanceled,revoked}.

Event → entitlement mapping:
- `order.paid` with `subscription_id == null` and
  `product_id == POLAR_PRODUCT_FOUNDER` and `metadata.plan == "founder"`
  → `record_founder_pass(provider="polar", provider_payment_id=order id,
  amount=total_amount)`. 409 = retry, idempotent-ok.
- `subscription.*` with `product_id == POLAR_PRODUCT_PREMIUM` →
  `upsert_subscription_by_provider_id` (provider="polar").
  Polar statuses kept verbatim: trialing/active/past_due/canceled;
  anything else (incomplete, unpaid, revoked, future) → canceled.
  `cancel_at_period_end` is a direct field;
  `current_period_start`/`current_period_end` direct fields.
  user_id from `metadata.user_id` (server-set at checkout creation).

## Tasks

1. **config.py**: delete `paddle_*`; add `polar_access_token`,
   `polar_webhook_secret`, `polar_product_founder`, `polar_product_premium`,
   `polar_api_base` (default `https://api.polar.sh`). ✅ when mypy passes.
2. **services/billing.py**: rewrite per above. `CheckoutSession{url: str}`;
   `create_checkout()` calls Polar via httpx (already a dependency),
   raises 503 when unconfigured (unchanged contract).
3. **api/routes/billing.py**: checkout route returns `{url}`; webhook route
   reads the three standard-webhooks headers.
4. **db/repositories/billing.py**: `record_founder_pass` provider param
   (default "polar").
5. **Tests** (`test_waitlist_and_billing_routes.py`): rewrite the 12 billing
   tests for Polar semantics (same scenarios: unconfigured 503, missing/bad
   sig 400, stale timestamp, founder grant + idempotent retry + product
   mismatch, sub-linked order ignored, subscription upsert / cancel flag /
   unknown-status→canceled). Checkout test mocks httpx. Green:
   `backend/.venv/Scripts/python -m pytest`, ruff, strict mypy.
6. **Frontend**: `lib/paddle.ts` → `lib/checkout.ts`
   (`redirectToCheckout(config: CheckoutSession)`); `types.ts`
   `CheckoutConfig` → `{url}`; `queries.ts` uses it; SubscriptionPage copy
   "Paddle" → "Polar" (payment-processor mentions); legal pages mention
   Paddle as MoR — update Terms/Privacy/Refunds MoR name to Polar.
   Remove `@paddle/paddle-js` from package.json. Green: eslint, tsc, vitest.
7. **Deploy**: `flyctl secrets set POLAR_*` (5 values) +
   `flyctl secrets unset PADDLE_*` from `backend/`; `flyctl deploy
   --remote-only`. Frontend `vercel deploy --prod` from `frontend/`
   (SW gotcha: unregister before verifying). Remove PADDLE_* from .env.
8. **Live E2E** (real account, no money): create 100%-off discount via API,
   fresh signup on hanvoice.app, buy Founder Pass with the code, assert
   webhook 200 in Polar dashboard + `founder_pass_purchases` row +
   founder UI state; archive the discount afterwards.
9. **Docs**: HANDOVER.md Paddle section → Polar (go-live steps collapse to
   "done"); memory update; conventional commit.

## Progress

- [x] Plan written
- [x] 1–4 backend code (config/service/routes/repo; provider="polar")
- [x] 5 backend green — 124 passed, ruff clean, strict mypy clean
- [x] 6 frontend — paddle.ts deleted, checkout = redirect to session.url,
      @paddle/paddle-js uninstalled, Terms/Privacy/Refunds/Subscription copy
      says Polar; eslint + tsc + 42 vitest green
- [~] 7 deploy — Fly secrets STAGED (POLAR_* set, PADDLE_* unset; take
      effect on next deploy). `flyctl deploy` blocked by session permissions
      → founder runs `flyctl deploy --remote-only` from backend/ then
      `vercel deploy --prod` from frontend/ (that order: API first).
- [ ] 8 E2E — after deploy: create 100%-off discount via API, fresh signup,
      buy Founder Pass free, assert webhook 200 + founder_pass_purchases row
      + founder UI; archive discount.
- [ ] 9 docs — HANDOVER updated alongside this commit; memory updated
