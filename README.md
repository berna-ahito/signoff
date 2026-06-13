<div align="center">

<!-- Replace the SVG below with your ChatGPT-generated banner once ready -->
<!-- Save the image as docs/banner.png and update the src -->
<img src="docs/logo.svg" alt="ProcureFlow AI" height="64" />

# ProcureFlow AI

**Purchase requests that actually get approved correctly.**

A full-stack AI-assisted procurement workflow system. Structured intake, role-based approval routing, AI risk classification, and a complete audit trail — with humans always in control of every decision.

[![Backend Tests](https://img.shields.io/badge/backend-160%20tests-brightgreen?style=flat-square)](https://github.com/berna-ahito/procureflow-ai)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen?style=flat-square)](https://github.com/berna-ahito/procureflow-ai)
[![Frontend Tests](https://img.shields.io/badge/frontend-36%20tests-brightgreen?style=flat-square)](https://github.com/berna-ahito/procureflow-ai)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## The problem this solves

Without a system, procurement lives in Slack threads and email chains. Requests get approved by whoever's available, not whoever's authorized. Spend goes untracked. Vendors get paid without anyone reviewing the quote.

ProcureFlow routes every purchase request through the right approval chain — manager for standard amounts, finance above a threshold — with an AI pre-review on each one and an append-only audit trail on every decision.

<div align="center">
<img src="docs/screenshots/login.png" alt="Login" width="49%" />
<img src="docs/screenshots/dashboard.png" alt="Dashboard" width="49%" />
<img src="docs/screenshots/request-form.png" alt="New request" width="49%" />
<img src="docs/screenshots/request-detail.png" alt="Request detail" width="49%" />
</div>

---

## Features

- **Intake** — structured purchase request form with drag-and-drop file attachments (5 MB / 5 file limits)
- **AI review** — provider-agnostic classification, risk scoring, and missing-field detection (MockProvider by default; swap for Gemini/Groq/Ollama)
- **Approval chain** — role-based routing (requester → manager → finance), full status-transition enforcement, audit log on every change
- **Procure-to-pay controls** — departments/budgets, vendor records, purchase orders, receiving, invoice verification, and request comments
- **RFQ drafting** — AI-generated request-for-quote text with one click
- **Admin panel** — user management, spend analytics by category, CSV-exportable summaries
- **Auth** — JWT access tokens + refresh tokens, RBAC, IDOR protection on every resource
=======
| | Feature | Details |
|---|---|---|
| 📋 | **Structured intake** | Form with validation, categorization, urgency, and drag-and-drop file attachments (5 MB / 5 file cap) |
| 🤖 | **AI review** | Risk classification, missing-field detection, and RFQ draft generation — advisory only, never approves |
| ✅ | **Approval routing** | Role-based chain: requester → manager → finance. Amount and category thresholds configurable by admin |
| 🔒 | **State machine** | Valid transitions enforced server-side. No request can skip steps or be approved by the wrong role |
| 📊 | **Analytics** | Spend by category, monthly trends, pipeline value — visible to admin and finance roles |
| 🔔 | **Notifications** | Email via Resend on submission and decision. Provider-swappable (mock logs to stdout if key not set) |
| 🗂️ | **Audit trail** | Every status change logged with actor, action, note, and timestamp. Append-only, no deletes |
| 🔐 | **Auth** | JWT access tokens (15 min) + server-side refresh tokens (7 days), RBAC, IDOR protection |

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · SQLAlchemy · Alembic |
| Database | PostgreSQL via Neon (SQLite in dev) |
| Frontend | React 18 · Vite · TypeScript |
| UI | shadcn/ui · Tailwind CSS · Motion |
| Charts | Recharts |
| AI | Groq API (MockProvider default — no key needed) |
| Tests | pytest · 144 passing · 95% coverage · Vitest · 35 passing |
| Deploy | Render (API) · Vercel (frontend) · Neon (database) |

---

## Quick start

**Prerequisites:** Python 3.11+, Node.js 20+

```bash
# Backend
py -m pip install -r requirements.txt
cp .env.example .env          # set SECRET_KEY at minimum
py -m alembic upgrade head
py scripts/seed.py            # loads demo data
py -m uvicorn app.main:app --reload
```

```bash
# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Demo credentials:

| Email | Password | Role |
|---|---|---|
| alice@test.com | alice123 | Requester |
| bob@test.com | bob123 | Manager |
| carol@test.com | carol123 | Finance |
| admin@test.com | admin123 | Admin |

---

## Security

- **IDOR/BOLA** — every resource goes through `_get_request_or_403`. Ownership verified per request, not inferred from session
- **No mass assignment** — separate `Create`, `Update`, and `AdminUpdate` schemas. Users cannot self-elevate role
- **Refresh tokens** — stored server-side, rotated on use, explicitly revoked on logout
- **AI output validation** — `risk_level` and `recommended_action` validated against an allowlist before persist
- **File uploads** — MIME type allowlist, filenames sanitized, 5 MB cap enforced before reading into memory
- **Rate limiting** — SlowAPI on all mutation and read endpoints. 5/min on login
- **Security headers** — `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` on every response
- **No docs in production** — `/docs`, `/redoc`, `/openapi.json` disabled when `APP_ENV=production`
- **Startup guards** — app refuses to start in production with a placeholder `SECRET_KEY`

---

## Deploy

### 1. Database — Neon (free tier)
Create a project at [neon.tech](https://neon.tech). Copy the connection string — this becomes your `DATABASE_URL`.

### 2. Backend — Render (free tier)
Connect the repo at [render.com](https://render.com). Render picks up `render.yaml` automatically.

Set these environment variables in the Render dashboard:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Neon connection string |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `GROQ_API_KEY` | Optional — AI reviews use mock provider if not set |
| `RESEND_API_KEY` | Optional — notifications log to stdout if not set |
| `CORS_ORIGINS` | Your Vercel frontend URL |
| `APP_ENV` | `production` |

### 3. Frontend — Vercel (free tier)
Import the repo at [vercel.com](https://vercel.com). Set root directory to `frontend/`. Add one env var:

```
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

`frontend/vercel.json` handles SPA routing automatically.

---

## Environment variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Production |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | Always |
| `GROQ_API_KEY` | AI review provider | Optional |
| `RESEND_API_KEY` | Email notifications | Optional |
| `CORS_ORIGINS` | Comma-separated allowed origins | Production |
| `APP_ENV` | Set to `production` to disable `/docs` | Production |

---

## Tests

```bash
# Backend (160 passing, 95% coverage)
py -m pytest --cov=app --cov-report=term-missing

# Frontend (36 passing)
cd frontend && npm test -- --run
```

Coverage target: ≥ 94% backend, all frontend test suites green.

## Project structure

```
procureflow-ai/
├── app/
│   ├── core/          # auth, deps, rate limiter, security
│   ├── db/            # SQLAlchemy models and session
│   ├── routers/       # FastAPI routers per domain
│   ├── schemas/       # Pydantic request/response models
│   └── services/      # AI review, approval engine, notifications
├── tests/             # pytest test suite
├── frontend/
│   ├── src/
│   │   ├── api/       # axios client + per-domain helpers
│   │   ├── components/# shared UI components
│   │   ├── pages/     # route-level page components
│   │   ├── lib/       # authStore, hooks
│   │   └── __tests__/ # Vitest unit tests
│   └── vercel.json
├── render.yaml
└── .env.example
```

## Deployment

### API → Render

1. Push to GitHub.
2. Create a **Web Service** on [render.com](https://render.com) and connect the repo.
3. Render picks up `render.yaml` automatically.
4. Set `SECRET_KEY` in the Render environment dashboard (mark as secret).

### Frontend → Vercel

1. Import the repo on [vercel.com](https://vercel.com) with root directory set to `frontend/`.
2. Set `VITE_API_BASE_URL` to your Render service URL.
3. `frontend/vercel.json` handles the SPA fallback rewrite.

## Security notes

- All endpoints require authentication; admin-only routes enforce `require_role("admin")`.
- IDOR/BOLA protection: every resource fetch verifies ownership or role.
- Refresh tokens are stored server-side and rotated on use.
- File downloads use `Content-Disposition: attachment` with sanitised filenames.
- Rate limiting is enabled on all mutation endpoints.
- No secrets committed; see `.env.example`.
- Purchase order export currently returns printable HTML from `/purchase-orders/{id}/pdf`; true PDF generation is future work unless a safe dependency is added.
=======
---

## License

MIT
