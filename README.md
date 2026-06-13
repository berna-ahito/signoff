# ProcureFlow AI

A portfolio-grade full-stack procurement workflow system. Turns messy purchase requests into structured, validated, auditable procurement data — with AI-assisted review and a human-in-the-loop approval chain.

## Features

- **Intake** — structured purchase request form with drag-and-drop file attachments (5 MB / 5 file limits)
- **AI review** — provider-agnostic classification, risk scoring, and missing-field detection (MockProvider by default; swap for Gemini/Groq/Ollama)
- **Approval chain** — role-based routing (requester → manager → finance), full status-transition enforcement, audit log on every change
- **Procure-to-pay controls** — departments/budgets, vendor records, purchase orders, receiving, invoice verification, and request comments
- **RFQ drafting** — AI-generated request-for-quote text with one click
- **Admin panel** — user management, spend analytics by category, CSV-exportable summaries
- **Auth** — JWT access tokens + refresh tokens, RBAC, IDOR protection on every resource

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite (dev) |
| Frontend | React 18 + Vite + TypeScript |
| UI | shadcn/ui + Tailwind CSS + motion |
| Charts | Recharts |
| Auth | JWT (python-jose) + bcrypt |
| Tests | pytest + Vitest + React Testing Library |
| Deployment | Render (API) + Vercel (frontend) |

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
py -m pip install -r requirements.txt
cp .env.example .env          # fill in SECRET_KEY
py -m uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

UI available at `http://localhost:5173`.

## Environment variables

### Backend (`.env`)

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` |
| `DATABASE_URL` | SQLAlchemy connection string (defaults to `sqlite:///./procureflow.db`) |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default `7`) |

### Frontend (`.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL |

## Running tests

```bash
# Backend
py -m pytest --cov=app --cov-report=term-missing

# Frontend
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

## License

MIT
