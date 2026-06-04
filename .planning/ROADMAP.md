# ProcureFlow AI — Roadmap

## Phase Summary

| Phase | Name | Status | Key Deliverable |
|-------|------|--------|-----------------|
| 0 | Planning & Architecture | DONE | .planning/ foundation, docs/ |
| 1 | 1/8 | In Progress|  |
| 2 | AI Review Service | TODO | MockProvider, AIReviewService, provider interface, tests |
| 3 | Frontend MVP | TODO | React+Vite, 3 screens, JWT auth flow, API integration |
| 4 | Security Hardening | TODO | IDOR audit, rate limiting, input hardening, security checklist |
| 5 | Integration Tests | TODO | Full-flow httpx tests, pytest coverage ≥80% |
| 6 | Deployment | TODO | Free-first deploy (backend + frontend) |
| 7 | Portfolio Polish | TODO | README, screenshots, case study |

---

## Phase 1 — Backend Foundation

**Goal:** Runnable FastAPI app with full DB schema, JWT auth, purchase request CRUD, approval rules engine, and audit logging. No AI yet.

**Done when:**
- `py -m uvicorn app.main:app` starts without error
- All DB tables created via Alembic migration
- JWT login returns token; protected endpoints reject invalid tokens
- Purchase request can be created, submitted, and routed to an approver role
- Approval decision (approve/reject/needs_more_info) changes status correctly
- Every status change writes an audit_log row
- `py -m pytest` passes with ≥80% coverage on approval engine and validation

**Deliverables:**
```
app/
  main.py
  core/
    config.py       # settings from .env
    security.py     # JWT encode/decode, password hash
    deps.py         # FastAPI dependency injection
  db/
    base.py         # SQLAlchemy engine + session
    models.py       # all ORM models
  schemas/
    user.py
    auth.py
    purchase_request.py
    approval.py
    audit.py
  routers/
    auth.py
    users.py
    requests.py
    approvals.py
    audit.py
  services/
    approval_engine.py   # rule evaluation + routing
    audit_service.py     # append-only audit writes
  alembic/
    versions/
      001_initial.py
tests/
  test_auth.py
  test_requests.py
  test_approval_engine.py
  test_idor.py
.env.example
requirements.txt
```

**Packages (justified):**
- `fastapi` — web framework
- `uvicorn` — ASGI server
- `sqlalchemy` — ORM
- `alembic` — migrations
- `python-jose[cryptography]` — JWT
- `passlib[bcrypt]` — password hashing
- `pydantic[email]` — validation + email type
- `python-dotenv` — env loading
- `httpx` — test client
- `pytest` — test runner
- `pytest-cov` — coverage

---

## Phase 2 — AI Review Service

**Goal:** Provider-agnostic AI review layer. MockProvider returns plausible structured output with confidence scores. Triggers on `pending_review`.

**Done when:**
- `AIReviewProvider` abstract interface defined
- `MockProvider` passes all provider tests
- AI review stored in `ai_reviews` table
- Request detail endpoint returns embedded AI review
- Provider can be swapped via config without changing business logic
- Tests cover MockProvider output schema and confidence score ranges

**Deliverables:**
```
app/
  services/
    ai_review/
      __init__.py
      base.py          # AIReviewProvider ABC
      mock_provider.py # deterministic mock
      service.py       # AIReviewService (calls provider, stores result)
      schemas.py       # AIReviewResult dataclass/Pydantic
tests/
  test_ai_review.py
```

---

## Phase 3 — Frontend MVP

**Goal:** React+Vite SPA with 3 screens, JWT auth, and full API integration.

**Done when:**
- Login screen authenticates and stores token
- Dashboard lists requests with status badges, filtered by role
- Submit form creates a purchase request
- Detail view shows all fields + AI review panel + approve/reject actions (role-gated)
- No hardcoded API URLs (use env variable)
- Works against local backend

**Deliverables:**
```
frontend/
  src/
    api/
      client.ts        # axios instance with auth header
      requests.ts
      auth.ts
      approvals.ts
    components/
      RequestCard.tsx
      AIReviewPanel.tsx
      StatusBadge.tsx
      ApprovalActions.tsx
    pages/
      LoginPage.tsx
      DashboardPage.tsx
      SubmitPage.tsx
      DetailPage.tsx
    hooks/
      useAuth.ts
      useRequests.ts
    App.tsx
    main.tsx
  index.html
  vite.config.ts
  .env.example
  package.json
```

---

## Phase 4 — Security Hardening

**Goal:** All security checklist items verified. Rate limiting added. IDOR audit complete.

**Done when:**
- Every request ID endpoint verified for ownership/role check
- Rate limiting active on `/auth/login` and `POST /requests`
- Input validation covers all edge cases (negative amounts, empty strings, SQL patterns)
- No secrets in repo (automated scan)
- SECURITY_CHECKLIST.md fully checked

**Packages added:**
- `slowapi` — rate limiting for FastAPI

---

## Phase 5 — Integration Tests

**Goal:** Full-flow httpx tests covering happy path + edge cases end-to-end against test DB.

**Done when:**
- Full requester → submit → AI review → approval decision flow tested
- IDOR tests pass (user A cannot see user B's request)
- Approval routing tested for each tier
- Coverage report ≥80% globally
- CI-ready: `py -m pytest --cov` passes clean

---

## Phase 6 — Deployment (Free-First)

**Goal:** Backend and frontend live on free tier hosting.

**Options (decide at time of execution):**
- Backend: Railway / Render / Fly.io free tier
- Frontend: Vercel / Netlify
- DB: SQLite file on backend host, or upgrade to Turso if SQLite-over-HTTP needed

**Done when:**
- Public URL works end-to-end
- `.env` values set as host environment secrets
- No secrets in repo

---

## Phase 7 — Portfolio Polish

**Goal:** Project presentable as portfolio piece.

**Done when:**
- README.md: what it is, why it matters, how to run, screenshots
- At least 3 screenshots or a short demo GIF
- ARCHITECTURE.md: data flow diagram (text or mermaid)
- Deployment URL in README
