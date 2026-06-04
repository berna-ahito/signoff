# ProcureFlow AI

AI-assisted procurement intake, approval routing, RFQ drafting, and audit system.

Turns messy employee purchase requests into structured, validated, auditable procurement data. AI classifies and summarizes — humans always approve or reject spending.

---

## Problem

Most small-to-mid orgs handle purchase requests over email or Slack. That means no audit trail, no consistent approval routing, no visibility into spend categories, and no way to draft RFQs at scale. ProcureFlow AI fixes this with a rules-driven backend and a pluggable AI review layer.

---

## Phase 1 Status — Complete

Backend foundation is done and tested.

| Area | Status |
|------|--------|
| DB schema (SQLite + Alembic migrations) | Done |
| JWT authentication | Done |
| User management | Done |
| Purchase request CRUD + submission | Done |
| Approval rules engine | Done |
| Approval routing (requester → manager/finance) | Done |
| Audit logging on every status change | Done |
| IDOR/BOLA protection | Done |
| Test suite (53 tests passing) | Done |

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI |
| ORM | SQLAlchemy (sync, SQLite-first) |
| Migrations | Alembic |
| Auth | python-jose + passlib (bcrypt) |
| Validation | Pydantic v2 |
| Tests | pytest + httpx |

---

## Setup

```bash
# Create and activate virtualenv
py -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

# Install dependencies
py -m pip install -r requirements.txt

# Configure environment
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
# Edit .env — set SECRET_KEY

# Run migrations
py -m alembic upgrade head

# Seed demo users (optional)
py scripts/seed.py

# Start server
py -m uvicorn app.main:app --reload
```

---

## Running Tests

```bash
py -m pytest
py -m pytest --cov=app --cov-report=term-missing
```

---

## Demo Users

After running `py scripts/seed.py`:

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | admin |
| manager@example.com | manager123 | manager |
| finance@example.com | finance123 | finance |
| user@example.com | user123 | requester |

---

## Roadmap

| Phase | Name | Status |
|-------|------|--------|
| 1 | Backend Foundation | **Done** |
| 2 | AI Review Layer | Next — MockProvider → Gemini/Groq/Ollama |
| 3 | Frontend MVP | React + Vite, 3 core screens |
| 4 | Security Hardening + Portfolio Packaging | Rate limiting, OWASP audit, case study |

---

## AI Boundary

AI may: classify requests, detect missing info, assess risk, summarize, draft RFQ text.

AI must never: approve or reject spending. That is always a human action.
