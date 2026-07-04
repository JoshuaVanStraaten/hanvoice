# Deployment

## The pieces

1. **Supabase** (managed) — database, auth, RLS. Apply `supabase/migrations/` and
   `supabase/seed.sql` via `supabase db push` + `supabase seed run` (or the SQL editor).
2. **Backend** — one container (`backend/Dockerfile`), stateless, port 8000.
3. **Frontend** — static files (`frontend/Dockerfile` → nginx, or any static host).

## Backend hosting

Any container host works; the app is a single stateless container:

- **Fly.io** — `fly launch` in `backend/`, set secrets with `fly secrets set`.
- **Railway / Render** — point at `backend/Dockerfile`, add env vars in the dashboard.

Set all required env vars (see the README table). Run **one uvicorn worker per
container** and scale with replicas — the in-process rate limiter assumes one
process; the Postgres daily quota stays correct across replicas either way.

Point Stripe's webhook at `https://<api-host>/api/billing/webhook` and set
`STRIPE_WEBHOOK_SECRET` from the endpoint's signing secret.

## Frontend hosting

The build is fully static. **Vite bakes `VITE_*` values into the bundle at build
time** — set them in the build environment, not at runtime.

- **Vercel / Netlify** — root `frontend/`, build `npm run build`, output `dist/`,
  SPA fallback to `index.html` (Netlify: `/* /index.html 200`). Set `VITE_API_URL`
  to the backend's public origin.
- **Same-origin option** — serve the nginx image behind the same domain as the API
  (proxy `/api` to the backend) and leave `VITE_API_URL` empty. Avoids CORS entirely.

If frontend and backend are on different origins, add the frontend origin to the
backend's `CORS_ORIGINS`.

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR: backend (ruff, mypy strict,
pytest) and frontend (eslint, tsc, vitest, build). Recommended flow: branch → PR →
green CI → merge to `main` → deploy hook (Fly/Railway auto-deploy on push, Vercel/
Netlify build on merge).

## Post-deploy checklist

- `GET /api/health` returns `{"status": "ok"}`.
- Sign up, pass one phrase, and confirm `/api/usage/today` increments.
- Stripe test-mode checkout completes and the webhook writes the subscription row.
- Lighthouse PWA check passes (installable, service worker active).
