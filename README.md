<div align="center">

<img src="docs/assets/signoff-header.svg" alt="Signoff — AI-assisted approval workflow" width="900">

**A demo procurement approval app for turning messy purchase requests into reviewed, routed, and auditable decisions.**

A demo procurement approval app for teams that need clearer purchase decisions.

Signoff turns purchase requests into a structured workflow: employees submit what they need, managers and finance review the right requests, AI flags missing details or risk, and every decision is saved in an audit trail.

This repo is built as a portfolio-grade full-stack application, not a production SaaS. It includes sample users and demo purchase data so reviewers can log in and test the workflow immediately.

[![Backend Tests](https://img.shields.io/badge/backend-170%20tests-brightgreen?style=flat-square)](https://github.com/berna-ahito/signoff)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen?style=flat-square)](https://github.com/berna-ahito/signoff)
[![Frontend Tests](https://img.shields.io/badge/frontend-38%20tests-brightgreen?style=flat-square)](https://github.com/berna-ahito/signoff)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## The problem this solves

Small teams often approve purchases through Slack, email, spreadsheets, or whoever happens to reply first. That makes it hard to answer basic questions:

* Who requested this?
* Who approved it?
* Was finance supposed to review it?
* What quote or file supported the decision?
* What changed after the request was submitted?

Signoff gives that process one place to live. A request moves from intake to review to approval, with role-based routing, AI-assisted checks, and an audit trail for every decision.

---

## Features

| Feature | Details |
|---|---|
| **Structured intake** | Form with validation, categorization, urgency, and drag-and-drop file attachments (5 MB / 5 file cap) |
| **AI review** | Risk classification, missing-field detection, and RFQ draft generation — advisory only, never approves |
| **Approval routing** | Role-based chain: requester → manager → finance. Amount and category thresholds configurable by admin |
| **State machine** | Valid transitions enforced server-side. No request can skip steps or be approved by the wrong role |
| **Analytics** | Spend by category, monthly trends, pipeline value — visible to admin and finance roles |
| **Notifications** | Email via Resend on submission and decision. Provider-swappable (mock logs to stdout if key not set) |
| **Audit trail** | Every status change logged with actor, action, note, and timestamp. Append-only, no deletes |
| **Auth** | JWT access tokens (15 min) + server-side refresh tokens (7 days), RBAC, IDOR protection |

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
| Tests | pytest · 170 passing · 95% coverage · Vitest · 38 passing |
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

Open `http://localhost:5173`.

---

## Demo data

The app includes sample users and sample purchase requests. The data is fake on purpose: it lets you test dashboards, approvals, statuses, and audit logs without creating everything from scratch.

Demo credentials:

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
- **Refresh tokens** — stored server-side, revoked on logout (rotation on refresh not implemented in current version)
- **AI output validation** — `risk_level` and `recommended_action` validated against an allowlist before persist
- **File uploads** — 5 MB cap enforced before reading into memory, count limited to 5; safe `Content-Disposition` headers on download
- **Rate limiting** — SlowAPI on all mutation and read endpoints. 5/min on login
- **Security headers** — `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` on every response
- **No docs in production** — `/docs`, `/redoc`, `/openapi.json` disabled when `APP_ENV=production`
- **Authentication** — all endpoints except `/health` require authentication; admin-only routes enforce `require_role("admin")`

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
# Backend (170 passing, 95% coverage)
py -m pytest --cov=app --cov-report=term-missing

# Frontend (38 passing)
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

## License

MIT — see [LICENSE](LICENSE).
