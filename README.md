# ProcureFlow AI

An AI-assisted procurement intake, approval-routing, and audit system built as a portfolio-grade full-stack application.

---

## What It Does

- **Purchase request intake** — Structured form with validation for title, category, urgency, cost, and justification
- **AI review** — Classifies risk level, detects missing information, and drafts RFQ text (advisory only)
- **Approval routing** — Configurable rules engine assigns requests to the correct role (manager, finance) based on category and amount
- **Full audit trail** — Every status change is logged with actor, timestamp, and note; append-only

---

## Why It Matters

ProcureFlow AI is built on a human-in-the-loop principle: the AI may classify, summarize, assess risk, and draft RFQ text, but it cannot approve or reject spending — that decision always belongs to an authorized human. The AI provider layer is abstracted behind an interface (`AIReviewProvider` ABC), so switching from the `MockProvider` to Groq or another provider requires only a config change. Security is treated as a first-class concern: IDOR protection, rate limiting, no mass assignment, and a JWT scheme with role-encoded tokens.

---

## Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + SQLAlchemy (SQLite) + Alembic |
| Frontend | React 18 + Vite + TypeScript + React Router v6 |
| Database | SQLite (local-first; swap to PostgreSQL via connection string) |
| AI | Provider-agnostic ABC — MockProvider default, GroqProvider available |
| Backend tests | pytest + httpx |
| Frontend tests | Vitest + React Testing Library |

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Requester | alice@test.com | alice123 |
| Manager | bob@test.com | bob123 |
| Finance | carol@test.com | carol123 |
| Admin | admin@test.com | admin123 |

---

## Quick Start

### Backend

```bash
# 1. Create and activate a virtual environment
py -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
py -m pip install -r requirements.txt

# 3. Create .env from template and set SECRET_KEY
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 4. Run database migrations
py -m alembic upgrade head

# 5. Seed demo users
py scripts/seed.py

# 6. Start the API server (port 8000)
py -m uvicorn app.main:app --reload
```

### Frontend

```bash
# From the project root
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

Open **http://localhost:5173** and sign in with any demo credential above.

---

## Running Tests

**Backend:**
```bash
py -m pytest
py -m pytest --cov=app --cov-report=term-missing
```

**Frontend:**
```bash
cd frontend
npm test
```

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full request lifecycle diagram and key architectural decisions.

---

## Security Highlights

- **IDOR/BOLA protection** — `_get_request_or_403` helper enforces ownership on every request-scoped endpoint; admin role bypasses for oversight
- **Rate limiting** — SlowAPI: 5 requests/min on `POST /auth/login` (brute-force), 20 requests/min on `POST /requests/` (spam)
- **JWT authentication** — 15-minute access tokens with `role` + `user_id` encoded in payload
- **No mass assignment** — Separate `Create`, `Update`, and `AdminUpdate` schemas prevent field injection
- **Audit log** — Every status transition creates an append-only `AuditLog` row with actor, action, and note
- **Secrets** — `.env.example` only; `.env` is gitignored and never committed

---

## Project Status

Locally runnable portfolio project. Deployment (Phase 6) deferred.
