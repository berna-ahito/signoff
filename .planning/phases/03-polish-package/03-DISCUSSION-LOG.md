# Phase 3: Polish + Package - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 03-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-06
**Phase:** 3-polish-package
**Areas discussed:** Admin pages scope, Rate limiting config, Frontend testing approach, Portfolio docs scope

---

## Admin Pages Scope

### Audit Log UI

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone /audit route | New admin-only page. Shows last 100 events globally. Matches GET /audit/. Admin nav link in Layout.tsx. | ✓ |
| Tab on DetailPage | Inline audit trail inside existing request detail. Uses GET /audit/requests/{id}. No new route. | |
| Both | Standalone page + per-request tab. Most complete but doubles scope. | |

**User's choice:** Standalone /audit route
**Notes:** Clean separation, matches existing backend endpoint, extends Layout.tsx nav pattern.

### User Management UI

| Option | Description | Selected |
|--------|-------------|----------|
| List + Create + Deactivate toggle | Full admin CRUD. POST /users/ for create, PATCH /users/{id} for is_active toggle. | ✓ |
| List + Create only | Show users and create-user form. No deactivate action. | |
| List only (read-only) | Just display existing users. Fastest to implement. | |

**User's choice:** List + Create + Deactivate toggle
**Notes:** All backend endpoints already exist. Demonstrates full admin capability for portfolio.

---

## Rate Limiting Config

### Endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| Login + POST /requests/ | Matches NFR-SEC-3: auth and submission endpoints. 5/min login, 20/min submission. | ✓ |
| Login only | Just POST /auth/login. Simpler. | |
| All write endpoints | Login, submission, approval, AI review. Maximum coverage. | |

**User's choice:** Login + POST /requests/
**Notes:** NFR-SEC-3 explicitly names both. Per-IP limiting using SlowAPI defaults.

### Test Safety Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Override to 1000/min in conftest.py fixture | Patches limiter key func. Zero changes to existing 79 tests. | ✓ |
| SLOWAPI_ENABLED env var toggle | Check env var; if False, limiter is a no-op. | |
| You decide | Implementation detail delegated to Claude. | |

**User's choice:** Override to 1000/min in conftest.py fixture
**Notes:** Protects all existing tests without touching them.

---

## Frontend Testing Approach

### Framework

| Option | Description | Selected |
|--------|-------------|----------|
| Vitest + React Testing Library | Integrates with Vite. Component-level tests. Mock axios. Fast. | ✓ |
| Playwright E2E only | Real browser tests. Requires backend or MSW. | |
| Both Vitest + Playwright | Full spectrum. More setup. | |

**User's choice:** Vitest + React Testing Library
**Notes:** Natural fit with existing Vite build system. No backend needed for test runs.

### Coverage Target

| Option | Description | Selected |
|--------|-------------|----------|
| 5-6 test files (hooks + key components) | useAuth, StatusBadge, ApprovalActions, AIReviewPanel, LoginPage, DashboardPage. Demonstrates competence. | ✓ |
| 80% coverage target | Full coverage. Extensive API mocking required. | |
| You decide | Pragmatic target for portfolio quality. | |

**User's choice:** 5-6 test files (prove competence)
**Notes:** Retrofitting 80% on existing untested code is disproportionate effort. Demonstrating the skill is sufficient.

---

## Portfolio Docs Scope

### Deliverables

| Option | Description | Selected |
|--------|-------------|----------|
| README.md | What + why + how to run. Essential. | ✓ |
| ARCHITECTURE.md with mermaid diagram | Request lifecycle data flow. Technical depth. | ✓ |
| Screenshots (static PNG files in /docs) | Login, Dashboard, Detail with AI panel, Admin pages. | ✓ |
| CASE_STUDY.md | Problem, decisions, AI boundary, security. Portfolio site copy. | ✓ |

**User's choice:** All four deliverables
**Notes:** Full portfolio documentation package.

### Audience

| Option | Description | Selected |
|--------|-------------|----------|
| Both technical + hiring manager | README for setup, ARCHITECTURE.md for depth. Serves both. | ✓ |
| Technical reviewer only | Deep dive architecture and security. | |
| Hiring manager only | Simple README, screenshots, no architecture detail. | |

**User's choice:** Both technical + hiring manager

---

## Claude's Discretion

- Exact column layout for AuditPage.tsx (which AuditLogResponse fields to display)
- Modal vs inline form for user creation in UserManagementPage.tsx
- Exact SlowAPI decorator placement (function decorator vs middleware)
- Vitest config details (coverage provider, reporter format)
- README formatting and section order

## Deferred Ideas

- Phase 5 (Integration Tests) — full httpx E2E suite; deferred, 79 unit tests sufficient
- Phase 6 (Deployment) — Railway/Render + Vercel; deferred to post-phase
- Demo GIF — high value but requires screen recording tools; screenshots sufficient for phase
- Per-request audit trail on DetailPage — deferred, standalone AuditPage covers requirement
- Groq integration tests — already deferred in Phase 2
