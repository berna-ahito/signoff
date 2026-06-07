# ProcureFlow AI — Case Study

## The Problem

Purchase requests in most small-to-mid-sized organizations are handled via email chains, Slack threads, or informal spreadsheets. This creates inconsistent approval workflows, missing audit trails, no standardized risk assessment, and no way to draft RFQs at scale. Finance teams lose visibility into spend categories; managers have no structured intake to route requests against; requesters get no feedback on why something was denied.

The challenge for this build was to demonstrate an AI-assisted intake system that stays within responsible bounds — AI recommends, humans decide — while being realistic and production-grade enough to use as a portfolio piece. The system had to handle real procurement concerns: approval routing by role and spend amount, an immutable audit trail, IDOR protection on financial data, and a pluggable AI layer that works without a paid API.

This is a portfolio project demonstrating production-grade patterns on a realistic domain. It is locally runnable and covers the full stack: FastAPI backend, React frontend, AI integration layer, and a test suite for both.

---

## Key Design Decisions

### AI Boundary Enforcement (Human-in-the-Loop)

**Decision:** AI may classify requests, detect missing information, assess risk level, and draft RFQ text. AI may not approve or reject spending.

**Rationale:** Prevents liability and maintains human accountability for financial commitments. Any AI system that touches money must have a clear human override point.

**Implementation:** The `recommended_action` field in the `ai_reviews` table is stored as advisory text (e.g., `manager_review`, `finance_review`). The approver's decision — `approved`, `rejected`, or `needs_more_info` — is recorded separately in the `AuditLog` and is the authoritative action that drives the status transition.

---

### Provider-Agnostic AI Layer

**Decision:** `AIReviewProvider` is an abstract base class. `MockProvider` is the default. `GroqProvider` is available and activated via config.

**Rationale:** No paid API dependency for development and testing. Real providers swap in with zero changes to business logic. This demonstrates a clean adapter pattern.

**Trade-off:** Mock output is deterministic, not truly intelligent. The mock always returns a fixed structure with realistic-looking data. This is adequate for demonstrating the architecture and running tests, but would not provide real value in production without a live provider.

---

### Configurable Approval Rules Engine

**Decision:** An `approval_rules` database table is evaluated at submit time. The first matching rule in priority order determines `assigned_role`. No approval thresholds are hardcoded.

**Rationale:** Hardcoded thresholds break when policies change. A rules table is auditable, testable, and lets admins update policy without a code deploy.

**Implementation:** Each rule has `priority`, `min_amount`, `max_amount`, `category` (nullable = wildcard), and `required_role`. The engine evaluates rules in ascending priority order and returns on the first match. No match → status `needs_rule` until an admin adds a covering rule.

---

### Security: IDOR + Rate Limiting + No Mass Assignment

**Decision:** `_get_request_or_403` helper on all request-scoped endpoints; SlowAPI per-IP rate limiting on login and submission; separate `RequestCreate`, `RequestUpdate`, and `AdminRequestUpdate` schemas.

**Rationale:** OWASP Top 10 compliance for a system that handles financial data. IDOR vulnerabilities are especially dangerous in multi-tenant approval workflows. Rate limiting prevents brute-force on login and submission spam.

**Trade-off:** Three separate schema classes add boilerplate. The alternative — a single schema with optional fields — opens the door to mass assignment attacks where a requester could set `assigned_role` or `status` directly.

---

### SQLite Local-First

**Decision:** SQLite via SQLAlchemy for local development. No PostgreSQL, no Docker, no external services.

**Rationale:** Zero infrastructure for portfolio demonstration. Alembic migrations mean a swap to PostgreSQL requires only a connection string change in `.env` — no schema changes needed.

**Trade-off:** SQLite has no concurrent write support and is not suitable for production multi-user workloads. Acceptable for a single-developer portfolio project where the goal is demonstrating patterns, not scaling.

---

## Security Measures

- **IDOR/BOLA guard** — `_get_request_or_403` enforces ownership on every request-scoped endpoint; admin role bypasses for operational oversight
- **Rate limiting** — SlowAPI: 5 req/min on `POST /auth/login` (brute-force protection), 20 req/min on `POST /requests/` (submission spam)
- **JWT authentication** — 15-minute access tokens; `role` + `user_id` encoded in payload; verified on every protected route
- **No mass assignment** — Separate `Create`, `Update`, and `AdminUpdate` Pydantic schemas; requesters cannot set `status` or `assigned_role` via the API
- **Audit log** — Every status transition appends an `AuditLog` row with `actor_id`, `action`, `old_status`, `new_status`, and `note`; rows are never updated or deleted
- **Password hashing** — bcrypt via passlib; plaintext passwords never stored or logged
- **Secrets management** — `.env.example` committed; `.env` gitignored; `SECRET_KEY` validated at startup
- **Status transition validation** — Only valid transitions are permitted (e.g., only `draft` can be submitted; only `pending_approval` can be decided on)

---

## Trade-offs Made

| Decision | Trade-off | Why Accepted |
|----------|-----------|--------------|
| MockProvider instead of real AI | Output is deterministic, not intelligent | Free, zero-latency, demonstrates the architecture correctly without paid API dependency |
| SQLite instead of PostgreSQL | No concurrent writes; not production-safe | Zero infrastructure; demonstrates Alembic migrations; easy to swap via connection string |
| localStorage for JWT | Vulnerable to XSS if CSP is not set | Acceptable for a portfolio piece; production would use httpOnly cookies with a CSRF token |
| No full integration test suite | Less coverage than ideal end-to-end | 79+ backend unit tests + 14 frontend tests covers core behaviors; httpx E2E tests deferred |
| No deployment | Not publicly accessible | Phase 6 (deployment) deferred; all patterns are locally demonstrable and verifiable |
