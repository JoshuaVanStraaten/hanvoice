---
name: verify
description: Build, run, and drive HanVoice locally to verify changes end-to-end (backend + PWA + live Supabase/Azure/NVIDIA).
---

# Verifying HanVoice

## Launch

- Backend: `cd backend; $env:PYTHONUTF8='1'; .venv\Scripts\python -m uvicorn app.main:app --port 8000`
  - **PYTHONUTF8=1 is required on Windows** — structlog lines containing Hangul
    crash requests with UnicodeEncodeError on a cp1252 console.
  - Port 8000 often has a **stale server** from an earlier session; probe a
    recently-added route first (404 = stale) and kill the listener:
    `Get-NetTCPConnection -LocalPort 8000 -State Listen` → `Stop-Process`.
- Frontend: `cd frontend; npm run dev` → http://localhost:5173 (vite proxies `/api` → :8000).
- Both `.env` files are wired to the live `hanvoice` Supabase project (`mxibibkcaarltsbkomvm`).

## Drive

- The Playwright MCP browser profile usually holds a logged-in session
  (test account `joshuavanstraaten100+hanvoice-test@gmail.com` / `hanvoice-test-1234`,
  founder-tier quotas). If "browser already in use": kill only chrome processes
  whose command line contains `ms-playwright-mcp`.
- Lessons player: `/lessons/<slug>` — explain/quiz advance via Continue;
  write blocks draw on the canvas with mouse drags (12px strokes are automatic).
- **The 8B vision judge scores synthetic mouse drawings near zero** — a failing
  write attempt still verifies the loop; don't burn retries chasing a pass.
- To pass a **speak** block deterministically: synthesize the phrase with Azure
  TTS as WAV (`X-Microsoft-OutputFormat: riff-16khz-16bit-mono-pcm`, voice
  `ko-KR-SunHiNeural`, key/region in `backend/.env`) and POST it to
  `/api/pronunciation/attempts` with `phrase_id` and the JWT from the browser's
  localStorage (`sb-*-auth-token` → `access_token`). Native audio scores ~97.
- Confirm progress server-side with Supabase MCP `execute_sql` against
  `lesson_block_progress` / `lesson_progress`.

## Gates (CI-equivalent, run before claiming done)

- Backend (from `backend/`): `.venv\Scripts\python -m ruff check .` · `-m mypy .` · `-m pytest`
- Frontend (from `frontend/`): `npm run lint` · `npm run typecheck` · `npm test` · `npm run build`
