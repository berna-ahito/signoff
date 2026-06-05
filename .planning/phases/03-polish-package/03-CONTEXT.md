# Phase 3: Polish + Package - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a complete, portfolio-ready ProcureFlow AI application. Scope:
1. **Frontend completion** — two remaining admin pages: standalone Audit Log page and User Management page (list + create + deactivate)
2. **Security hardening** — SlowAPI rate limiting on `POST /auth/login` and `POST /requests/`, OWASP checklist pass
3. **Frontend testing** — Vitest + React Testing Library setup, 5-6 test files covering hooks and key components
4. **Portfolio documentation** — README, ARCHITECTURE.md (mermaid), screenshots, CASE_STUDY.md

This is the final phase. Phases 3 (Frontend MVP), 4 (Security Hardening), and 7 (Portfolio Polish) from the original ROADMAP are merged here.

</domain>

<decisions>
## Implementation Decisions

### Admin Pages (Frontend)

- **D-01:** Audit log UI = **standalone `/audit` route**, admin-only. Fetches `GET /audit/` (last 100 global events). Add a role-gated nav link in `Layout.tsx`. New file: `AuditPage.tsx`.
- **D-02:** User management UI = **standalone `/users` route**, admin-only. Shows user list + create-user form + deactivate toggle (`is_active`). Calls `GET /users/` (if endpoint added), `POST /users/`, `PATCH /users/{id}`. New file: `UserManagementPage.tsx`.
- **D-03:** Both admin pages are role-gated to `admin` only. Non-admin users who navigate to these routes should see a 403/redirect, consistent with how existing role-gated actions work.

### Rate Limiting (Backend)

- **D-04:** Add `slowapi` to `requirements.txt`. Apply rate limiting on exactly two endpoints: `POST /auth/login` (5 req/min per IP) and `POST /requests/` (20 req/min per IP).
- **D-05:** Rate limiting = **per-IP** using SlowAPI's default key function (no user-based key needed for MVP).
- **D-06:** Keep 79 existing backend tests green: add a pytest conftest fixture that patches/overrides the limiter to allow 1000 req/min during tests. No changes to existing test files.

### Frontend Testing

- **D-07:** Framework = **Vitest + React Testing Library**. Integrates with existing Vite setup. Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` to `devDependencies`. Configure via `vite.config.ts` test block.
- **D-08:** Coverage target = **5-6 test files** covering: `useAuth.ts`, `StatusBadge.tsx`, `ApprovalActions.tsx`, `AIReviewPanel.tsx`, `LoginPage.tsx` (form submit + mock axios), and one page with mock API data (DashboardPage or AuditPage). Goal is demonstrating testing competence, not retrofitting 80% on existing code.
- **D-09:** Mock axios at the module level (`vi.mock('axios')`). No MSW, no backend required to run frontend tests.

### Portfolio Documentation

- **D-10:** Produce four docs: `README.md` (root), `docs/ARCHITECTURE.md`, `docs/screenshots/` (static PNGs), `docs/CASE_STUDY.md`.
- **D-11:** README covers: what it is, why it matters, role-based demo credentials (seeded users), setup steps (`py -m uvicorn`, `npm run dev`), stack overview, link to ARCHITECTURE.md.
- **D-12:** ARCHITECTURE.md uses mermaid diagram showing the full request lifecycle: submit → AI review → approval routing → decision → audit log. Target audience = technical reviewer.
- **D-13:** CASE_STUDY.md covers: the problem, key design decisions (AI boundary / human-in-the-loop, approval rules engine, provider-agnostic AI), security measures, trade-offs made. Target audience = portfolio site / hiring manager.
- **D-14:** Screenshots: Login page, Dashboard (with status badges), Detail page (with AI review panel), Admin audit log page, Admin user management page. Saved as PNG files in `docs/screenshots/`.

### Claude's Discretion

- Exact column layout for AuditPage.tsx (which columns from `AuditLogResponse` to display, column order)
- Modal vs inline form for user creation in UserManagementPage.tsx
- Exact SlowAPI decorator placement (on router function vs FastAPI middleware)
- Vitest config details (coverage provider, reporter format)
- README formatting and section order

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Foundation
- `.planning/ROADMAP.md` — Original phases 3+4+7 specs merged into this phase
- `.planning/PROJECT.md` — Product constraints (free APIs only, Windows dev, humans approve/reject)
- `.planning/REQUIREMENTS.md` — FR-FRONTEND-1 through FR-FRONTEND-5, FR-AUDIT-4, FR-USERS-3, NFR-SEC-3, NFR-TEST-1

### Existing Frontend Code (read before writing new pages)
- `frontend/src/pages/DashboardPage.tsx` — Existing page pattern (API call structure, role checks, JSX layout)
- `frontend/src/components/Layout.tsx` — Nav structure. Add admin nav links here.
- `frontend/src/api/client.ts` — Axios instance with auth header. Use for new admin API calls.
- `frontend/src/hooks/useAuth.ts` — Auth hook. Role checks come from here.
- `frontend/src/types.ts` — Shared TypeScript types. Add `User`, `AuditLog` types here if missing.

### Backend Endpoints Available (no new backend work required for pages)
- `app/routers/audit.py` — `GET /audit/` (last 100), `GET /audit/requests/{id}` — admin-only
- `app/routers/users.py` — `POST /users/` (create), `PATCH /users/{id}` (update), `GET /users/me`
- `app/schemas/audit.py` — `AuditLogResponse` schema (fields for UI columns)
- `app/schemas/user.py` — `UserResponse`, `UserCreate`, `UserAdminUpdate` schemas

### Rate Limiting Reference
- `app/main.py` — Entry point. SlowAPI limiter attached here (or per-router).
- `app/routers/auth.py` — `POST /auth/login` — rate limit target
- `app/routers/requests.py` — `POST /requests/` — rate limit target
- `tests/conftest.py` — Add rate limiter override fixture here. Do NOT modify existing tests.

### Phase 2 Established Patterns
- `.planning/phases/02-ai-review-service/02-CONTEXT.md` — Classical Column ORM, _now() default, Pydantic v2 model_validate, per-IP rate limiting rationale

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DashboardPage.tsx` — Copy API fetch pattern (`useEffect` + `useState` + axios call + error state). Use as template for AuditPage and UserManagementPage.
- `StatusBadge.tsx` + `StatusBadge.css` — Existing status display component. Reuse for audit log status column.
- `ApprovalActions.tsx` — Role-gated action buttons. Reference pattern for admin-only deactivate button.
- `Layout.tsx` — Nav links array. Extend with admin section (conditional on role === "admin").
- `useAuth.ts` — Returns `{ user, token, logout }`. `user.role` used for conditional rendering.

### Established Patterns
- Role-gating: `{user?.role === "admin" && <AdminNav />}` pattern already in Layout
- API calls: axios instance from `api/client.ts` with Bearer token automatically attached
- Error handling: `useState<string | null>` for error display, shown inline
- No Redux, no global state manager — React local state + hooks only

### Integration Points
- `AuditPage.tsx` → `GET /audit/` → `AuditLogResponse[]` from `app/routers/audit.py`
- `UserManagementPage.tsx` → `POST /users/` + `PATCH /users/{id}` → from `app/routers/users.py`
- `Layout.tsx` → add conditional admin nav links for `/audit` and `/users`
- `App.tsx` → add routes for `/audit` and `/users` (protected, admin-only redirect)
- `conftest.py` → add SlowAPI limiter override fixture
- `requirements.txt` → add `slowapi`
- `frontend/package.json` → add vitest + @testing-library/* to devDependencies
- `frontend/vite.config.ts` → add test: { environment: "jsdom" } block

### Note: Backend GET /users/ endpoint
- Current `users.py` only has `GET /users/me`, `POST /users/`, `PATCH /users/{id}`.
- A `GET /users/` list endpoint (admin-only) is needed for UserManagementPage. This is a new backend endpoint but small scope (1 function, admin-only).

</code_context>

<specifics>
## Specific Ideas

- Audit log table columns: `created_at`, `action`, `actor_id` (or actor name if joined), `old_status → new_status`, `note`. Keep it simple — no filtering needed for MVP.
- User management table: `email`, `full_name`, `role`, `department_id`, `is_active` (toggle). Create form: email, full_name, password, role, department_id fields.
- SlowAPI limits: 5/minute on login (brute-force threshold), 20/minute on submission (anti-spam threshold).
- Vitest test pattern: Arrange-Act-Assert per `common/testing.md`. Each test file has a clear describe block.
- Portfolio docs audience: primary = hiring manager + technical reviewer. No deployment URL needed (Phase 6 is deferred/dropped as separate phase).

</specifics>

<deferred>
## Deferred Ideas

- **Phase 5 (Integration Tests)** from original ROADMAP — full httpx integration test suite, E2E flow testing. Deferred; 79 unit tests sufficient for portfolio.
- **Phase 6 (Deployment)** from original ROADMAP — free-tier hosting (Railway/Render + Vercel). Deferred; this phase produces a locally-runnable portfolio piece with clear deploy instructions in README.
- **GIF demo** — High value for portfolio but requires screen recording + conversion tools on Windows. Deferred post-phase; screenshots are sufficient for the phase deliverable.
- **Per-request audit trail on DetailPage** — Discussed, deferred. Standalone AuditPage covers the requirement.
- **Groq integration tests** — Already deferred in Phase 2 context.

</deferred>

---

*Phase: 3-Polish + Package*
*Context gathered: 2026-06-06*
