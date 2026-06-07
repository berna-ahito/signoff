# Phase 3: Polish + Package - Research

**Researched:** 2026-06-06
**Domain:** Frontend completion (React/Vite/TypeScript), SlowAPI rate limiting (FastAPI), Vitest + React Testing Library, portfolio documentation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Audit log UI = standalone `/audit` route, admin-only. Fetches `GET /audit/` (last 100 global events). Add a role-gated nav link in `Layout.tsx`. New file: `AuditPage.tsx`.
- **D-02:** User management UI = standalone `/users` route, admin-only. Shows user list + create-user form + deactivate toggle (`is_active`). Calls `GET /users/` (if endpoint added), `POST /users/`, `PATCH /users/{id}`. New file: `UserManagementPage.tsx`.
- **D-03:** Both admin pages are role-gated to `admin` only. Non-admin users who navigate to these routes should see a 403/redirect.
- **D-04:** Add `slowapi` to `requirements.txt`. Apply rate limiting on exactly two endpoints: `POST /auth/login` (5 req/min per IP) and `POST /requests/` (20 req/min per IP).
- **D-05:** Rate limiting = per-IP using SlowAPI's default key function (`get_remote_address`).
- **D-06:** Keep 79 existing backend tests green: add a pytest conftest fixture that overrides the limiter to allow 1000 req/min during tests. No changes to existing test files.
- **D-07:** Framework = Vitest + React Testing Library. Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` to `devDependencies`. Configure via `vite.config.ts` test block.
- **D-08:** Coverage target = 5-6 test files covering: `useAuth.ts`, `StatusBadge.tsx`, `ApprovalActions.tsx`, `AIReviewPanel.tsx`, `LoginPage.tsx`, and one page with mock API data (DashboardPage or AuditPage).
- **D-09:** Mock axios at the module level (`vi.mock('axios')`). No MSW, no backend required.
- **D-10:** Produce four docs: `README.md` (root), `docs/ARCHITECTURE.md`, `docs/screenshots/` (static PNGs), `docs/CASE_STUDY.md`.
- **D-11:** README covers: what it is, why it matters, role-based demo credentials, setup steps, stack overview, link to ARCHITECTURE.md.
- **D-12:** ARCHITECTURE.md uses mermaid diagram showing full request lifecycle: submit → AI review → approval routing → decision → audit log.
- **D-13:** CASE_STUDY.md covers: the problem, key design decisions, security measures, trade-offs.
- **D-14:** Screenshots: Login, Dashboard, Detail, Admin audit log, Admin user management — saved as PNG in `docs/screenshots/`.

### Claude's Discretion

- Exact column layout for AuditPage.tsx
- Modal vs inline form for user creation in UserManagementPage.tsx
- Exact SlowAPI decorator placement (on router function vs FastAPI middleware)
- Vitest config details (coverage provider, reporter format)
- README formatting and section order

### Deferred Ideas (OUT OF SCOPE)

- Phase 5 Integration Tests (full httpx E2E suite)
- Phase 6 Deployment (Railway/Render/Vercel)
- GIF demo (screenshots sufficient)
- Per-request audit trail on DetailPage
- Groq integration tests
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FR-USERS-3 | Admin can create/deactivate users | `GET /users/` endpoint (NEW), `POST /users/`, `PATCH /users/{id}` are all present in `users.py`; `UserManagementPage.tsx` is the frontend surface |
| FR-AUDIT-4 | Audit log visible to admin | `GET /audit/` endpoint confirmed in `audit.py`; `AuditLogResponse` schema confirmed; `AuditPage.tsx` is the frontend surface |
| FR-FE-1 | Login screen | `LoginPage.tsx` — already complete; no changes needed |
| FR-FE-2 | Dashboard (list + status badges + filters) | `DashboardPage.tsx` — already complete; no changes needed |
| FR-FE-3 | Submit request form | `SubmitPage.tsx` — already complete (out of scope for this phase) |
| FR-FE-4 | Request detail view + AI review panel + approval actions | `DetailPage.tsx` — already complete (out of scope for this phase) |
| FR-FE-5 | Role-aware rendering | Already implemented via `user.role` checks; extend pattern for admin-only nav links |
| NFR-SEC-3 | Rate limiting on auth and submission endpoints | SlowAPI `@limiter.limit()` on `POST /auth/login` and `POST /requests/` |
| NFR-TEST-1 | 80% coverage minimum on approval engine/validation | Already met (79 backend tests); frontend tests are additive portfolio demos |
</phase_requirements>

---

## Summary

Phase 3 is a convergence phase that completes three parallel workstreams — frontend admin pages, backend rate limiting, and frontend testing — then wraps the project in portfolio documentation. The codebase is in good shape: 79 backend tests green, a well-structured FastAPI backend with IDOR protection, Pydantic v2 schemas, and a polished React+Vite SPA.

The four workstreams are largely independent and can be planned as separate waves. The only hard dependency: `GET /users/` endpoint (one new backend route) must land before `UserManagementPage.tsx` can be tested end-to-end. The SlowAPI integration touches three files (`main.py`, `auth.py`, `requests.py`, `conftest.py`) and must be planned carefully to avoid breaking the 79 passing tests.

Frontend testing is greenfield — zero test files exist today. Vitest integrates with the existing Vite setup via a single `test` block in `vite.config.ts`. All tests mock axios at module level; no backend is needed at test time.

Portfolio documentation builds on the existing `README.md` (currently Phase 1 status), `docs/SECURITY_CHECKLIST.md`, and `docs/SPEC.md`. The README needs a full rewrite for portfolio presentation; ARCHITECTURE.md and CASE_STUDY.md are new files.

**Primary recommendation:** Execute in four waves — (1) backend: `GET /users/` + SlowAPI, (2) frontend: AuditPage + UserManagementPage + nav/routing wiring, (3) frontend tests: Vitest setup + 5-6 test files, (4) docs: README rewrite + ARCHITECTURE.md + CASE_STUDY.md.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Audit log display | Frontend (SPA) | API (data source) | Admin-only read-only view; no mutations |
| User list + create + deactivate | Frontend (SPA) | API (CRUD owner) | Frontend renders, API enforces admin role + hashes password |
| GET /users/ list endpoint | API/Backend | — | New admin-only endpoint; IDOR-free because admin sees all users |
| Rate limiting per IP | API/Backend | — | Must happen server-side; cannot be enforced client-side |
| Admin route gating (403/redirect) | Frontend (SPA) | — | Role from decoded JWT; navigate('/dashboard') on role mismatch |
| Frontend test mocking | Test layer | — | vi.mock('axios') at module level; no backend dependency |
| Portfolio docs | Docs layer | — | Static markdown + mermaid; no runtime dependency |

---

## Standard Stack

### Backend (Rate Limiting)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| slowapi | 0.1.9 | Per-IP rate limiting for FastAPI/Starlette endpoints | Only mature rate-limiting library adapted from flask-limiter for Starlette; handles `RateLimitExceeded` via built-in exception handler [VERIFIED: PyPI registry + pypi.org/project/slowapi/] |

### Frontend (Testing)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vitest | 4.1.8 | Test runner integrated with Vite | Native Vite integration; uses same config; supports vi.mock() [VERIFIED: npm registry] |
| @testing-library/react | 16.3.2 | React component testing utilities | Industry standard for testing React components by behavior, not implementation [VERIFIED: npm registry] |
| @testing-library/jest-dom | 6.9.1 | Custom DOM matchers (toBeInTheDocument, etc.) | Extends vitest matchers with readable DOM assertions [VERIFIED: npm registry] |
| @testing-library/user-event | 14.6.1 | Simulates real user interactions | Preferred over fireEvent for realistic event simulation [VERIFIED: npm registry] |
| jsdom | 29.1.1 | Browser DOM simulation for Node.js | Required environment for component tests without a real browser [VERIFIED: npm registry] |

**Installation (frontend):**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**Installation (backend):**
```bash
py -m pip install slowapi
```

**Version verification performed:** npm registry queried directly — all versions confirmed as of 2026-06-06. slowapi 0.1.9 confirmed on PyPI.

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| slowapi | PyPI | ~5 yrs | established | github.com/laurentS/slowapi | N/A | Approved — well-known, referenced in FastAPI ecosystem docs |
| vitest | npm | ~3 yrs | tens of millions/wk | github.com/vitest-dev/vitest | N/A | Approved — Vite team maintained |
| @testing-library/react | npm | ~7 yrs | 50M+/wk | github.com/testing-library/react-testing-library | N/A | Approved — industry standard |
| @testing-library/jest-dom | npm | ~6 yrs | 50M+/wk | github.com/testing-library/jest-dom | N/A | Approved |
| @testing-library/user-event | npm | ~6 yrs | 30M+/wk | github.com/testing-library/user-event | N/A | Approved |
| jsdom | npm | ~12 yrs | 80M+/wk | github.com/jsdom/jsdom | N/A | Approved |

**slopcheck was unavailable at research time.** All packages are well-established with long history, high download counts, and official source repositories confirmed via PyPI and npm registry. All are [ASSUMED] by protocol but carry HIGH practical confidence based on multi-source verification.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
[Browser: Admin user]
    |
    | GET /audit/ or GET /users/ (Bearer token)
    v
[FastAPI app (main.py)]
    |-- SlowAPI limiter (IP-based, on POST /auth/login + POST /requests/)
    |-- CORSMiddleware (localhost:5173)
    |
    |-- /audit router -> AuditLog ORM -> SQLite
    |-- /users router -> User ORM -> SQLite
    |                  (NEW: GET /users/ admin list)
    |
    v
[React SPA (Vite)]
    |-- AuditPage.tsx -> GET /audit/ -> renders table
    |-- UserManagementPage.tsx -> GET /users/ + POST /users/ + PATCH /users/{id}
    |-- Layout.tsx -> conditional admin nav links (role === 'admin')
    |-- App.tsx -> /audit + /users routes (RequireAdmin guard)
```

### Recommended Project Structure (additions only)

```
frontend/src/
  pages/
    AuditPage.tsx          # NEW — admin-only audit log view
    UserManagementPage.tsx # NEW — admin-only user list+create+deactivate
  api/
    users.ts               # NEW — listUsers(), createUser(), updateUser()
    audit.ts               # NEW — listAuditLogs()
  __tests__/               # NEW — all test files live here
    useAuth.test.ts
    StatusBadge.test.tsx
    ApprovalActions.test.tsx
    AIReviewPanel.test.tsx
    LoginPage.test.tsx
    AuditPage.test.tsx     # or DashboardPage.test.tsx
  setup.ts                 # NEW — global test setup (jest-dom matchers)

app/routers/
  users.py                 # MODIFIED — add GET /users/ endpoint
  auth.py                  # MODIFIED — add @limiter.limit("5/minute")
  requests.py              # MODIFIED — add @limiter.limit("20/minute")

app/
  main.py                  # MODIFIED — attach SlowAPI limiter

tests/
  conftest.py              # MODIFIED — add limiter override fixture

docs/
  ARCHITECTURE.md          # NEW
  CASE_STUDY.md            # NEW
  screenshots/             # NEW dir — 5 PNG files

README.md                  # REWRITE — portfolio-grade
requirements.txt           # MODIFIED — add slowapi
```

### Pattern 1: SlowAPI Integration in FastAPI

**What:** Attach `Limiter` to FastAPI app state, register exception handler, decorate endpoints.
**When to use:** Any endpoint needing per-IP rate limiting.

```python
# app/main.py — add these lines
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ProcureFlow AI", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# app/routers/auth.py — add Request parameter + decorator
from fastapi import Request
from app.main import limiter  # import the singleton

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    ...
```

**Critical:** The `request: Request` parameter MUST be present in the function signature for SlowAPI to extract the client IP. Without it, SlowAPI cannot determine the rate limit key.

**Critical:** The route decorator (`@router.post`) must be ABOVE the `@limiter.limit()` decorator. Wrong order causes the limit to be silently ignored. [CITED: slowapi.readthedocs.io]

### Pattern 2: SlowAPI Disable in Pytest

**What:** Override `limiter.enabled = False` inside a conftest fixture so tests aren't throttled.
**When to use:** Any test session running against the FastAPI app with SlowAPI attached.

```python
# tests/conftest.py — add this fixture (does NOT touch existing fixtures)
import pytest
from app.main import limiter

@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """Override rate limiter for test isolation — sets 1000/min effectively."""
    limiter.enabled = False
    yield
    limiter.enabled = True
```

[CITED: github.com/laurentS/slowapi docs/examples.md — `limiter.enabled = False` is the documented approach]

**Note on circular import:** `limiter` must be defined in `app/main.py` (or a dedicated `app/core/limiter.py`) and imported by routers. The current `app/main.py` imports routers; routers importing back from `main.py` creates a circular import. **Recommended:** Move `limiter` to `app/core/limiter.py` and import from there in both `main.py` and routers. [ASSUMED — standard pattern to avoid circular imports; applies to this codebase based on current main.py structure]

```python
# app/core/limiter.py (NEW FILE — avoids circular import)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

```python
# app/main.py — import from core
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# app/routers/auth.py — import from core
from app.core.limiter import limiter
```

### Pattern 3: New GET /users/ Endpoint (admin-only)

**What:** List all users; admin role required. Mirrors existing `GET /audit/` pattern exactly.
**When to use:** UserManagementPage.tsx data source.

```python
# app/routers/users.py — add after existing endpoints
@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse.model_validate(u) for u in users]
```

**Security:** `require_role("admin")` dependency — confirmed present in `app/core/deps.py`. Non-admin → 403 automatically.

### Pattern 4: Admin Route Guard in React

**What:** Redirect non-admin users away from `/audit` and `/users`.
**When to use:** Any admin-only page in App.tsx.

```tsx
// In App.tsx — RequireAdmin guard (follows same pattern as RequireAuth)
function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

// Route usage
<Route path="/audit" element={<RequireAdmin><AuditPage /></RequireAdmin>} />
<Route path="/users" element={<RequireAdmin><UserManagementPage /></RequireAdmin>} />
```

**PAGE_TITLES** must also be extended:
```tsx
const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/submit': 'New Request',
  '/audit': 'Audit Log',       // NEW
  '/users': 'User Management', // NEW
}
```

### Pattern 5: Admin Nav Links in Layout.tsx

**What:** Conditional admin section in sidebar nav.
**When to use:** Extend sidebar when `role === 'admin'`.

```tsx
// In Layout.tsx sidebar-nav section, after existing nav links
{role === 'admin' && (
  <>
    <div className="nav-section-label">Admin</div>
    <NavLink to="/audit" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeNav}>
      {/* shield icon svg */}
      Audit Log
    </NavLink>
    <NavLink to="/users" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={closeNav}>
      {/* users icon svg */}
      Users
    </NavLink>
  </>
)}
```

### Pattern 6: AuditPage.tsx — Table Structure

**What:** Fetch `GET /audit/` and render as table. Data source: `AuditLogResponse[]`.
**Fields to display:** `created_at`, `action`, `actor_id`, `old_status → new_status`, `note`.

```tsx
// AuditPage.tsx follows DashboardPage.tsx pattern exactly
// useEffect + useState + apiClient.get('/audit/') + error/loading states
// Table columns: Time | Action | Actor ID | Status Change | Note
```

**AuditLogResponse** schema (from `app/schemas/audit.py`):
- `id: int`, `request_id: int`, `actor_id: Optional[int]`, `action: str`
- `old_status: Optional[str]`, `new_status: Optional[str]`, `note: Optional[str]`, `created_at: datetime`

**Types needed in `types.ts`:**
```typescript
export interface AuditLog {
  id: number
  request_id: number
  actor_id: number | null
  action: string
  old_status: string | null
  new_status: string | null
  note: string | null
  created_at: string
}
```

### Pattern 7: UserManagementPage.tsx — List + Create + Deactivate

**What:** Table of users + inline create form (below table) + deactivate toggle button per row.
**User type needed in `types.ts`:**
```typescript
export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  department_id: number | null
  is_active: boolean
  created_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
  role: Role
  department_id?: number
}
```

**API calls pattern (new file `frontend/src/api/users.ts`):**
```typescript
export async function listUsers(): Promise<User[]>    // GET /users/
export async function createUser(body: UserCreate): Promise<User>  // POST /users/
export async function updateUser(id: number, body: Partial<UserAdminUpdate>): Promise<User>  // PATCH /users/{id}
```

**Deactivate toggle:** `PATCH /users/{id}` with `{ is_active: false }` — uses existing `UserAdminUpdate` schema which already includes `is_active: Optional[bool]`.

### Pattern 8: Vitest Configuration

**What:** Add `test` block to `vite.config.ts` to enable Vitest with jsdom environment.

```typescript
// vite.config.ts — full replacement
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setup.ts'],
    css: false,
  },
})
```

```typescript
// frontend/src/setup.ts — global test setup
import '@testing-library/jest-dom'
```

**package.json scripts addition:**
```json
"test": "vitest run",
"test:watch": "vitest",
"test:ui": "vitest --ui"
```

**TypeScript config:** `tsconfig.json` must include `"types": ["vitest/globals"]` in `compilerOptions` to get `describe`, `it`, `expect`, `vi` without import.

### Pattern 9: Vitest + React Testing Library Mock Pattern

**What:** vi.mock('axios') at module level; mock return values per test.
**Critical:** Must mock the `default` export of axios (the axios instance), not named exports.

```tsx
// Example: LoginPage.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { LoginPage } from '../pages/LoginPage'

vi.mock('axios')

describe('LoginPage', () => {
  it('calls onLogin with email and password on submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue('requester')
    render(
      <MemoryRouter>
        <LoginPage onLogin={mockLogin} />
      </MemoryRouter>
    )
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@test.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'alice123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('alice@test.com', 'alice123'))
  })
})
```

**Note on `useAuth.ts` testing:** `useAuth` uses `localStorage` and calls `apiLogin`. To test it in isolation, mock `../api/auth`:
```tsx
vi.mock('../api/auth', () => ({ login: vi.fn() }))
```
Use `renderHook` from `@testing-library/react` to test hooks.

**Note on component wrapping:** All components that use `useNavigate` or `NavLink` require wrapping in `<MemoryRouter>` in tests.

**Note on `ApprovalActions` tests:** Component returns null when `canDecide` is false. Test must provide a request in `pending_approval` status with a role that matches to exercise the form path.

### Anti-Patterns to Avoid

- **Importing limiter from main.py in routers:** Creates circular imports. Use `app/core/limiter.py` as the singleton location.
- **Missing `request: Request` parameter:** SlowAPI silently fails to rate-limit if `request` is not the first positional FastAPI argument.
- **Wrong decorator order:** `@router.post` must be ABOVE `@limiter.limit()`. Reversed order means the limit is never applied.
- **Not wrapping hooks test components in MemoryRouter:** `useNavigate` throws outside Router context.
- **Testing `useAuth` by calling `login()` without mocking `localStorage`:** jsdom supports localStorage; no special mock needed — but `apiLogin` (the axios call) must be mocked.
- **Using `fireEvent.submit` instead of clicking the submit button:** For coverage, prefer clicking the button element with `disabled` attribute checks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-IP rate limiting | Custom middleware counting IPs | `slowapi` with `get_remote_address` | Race conditions, edge cases with proxies, 429 response formatting |
| DOM matchers in tests | `expect(el.className).toContain(...)` | `@testing-library/jest-dom` toBeInTheDocument, toHaveClass | Readable, maintained, handles edge cases |
| User interaction simulation | `fireEvent` for complex flows | `@testing-library/user-event` | Models real browser events including focus, keyboard order |
| Browser DOM in Node.js | Custom DOM shim | `jsdom` via Vitest `environment: 'jsdom'` | Complete spec-compliant implementation |
| Admin role checking | Custom middleware on every route | `require_role("admin")` dependency (already exists in deps.py) | Already implemented, tested |

**Key insight:** The project already has `require_role` in `app/core/deps.py` — every new admin endpoint just passes `current_user: User = Depends(require_role("admin"))` and role enforcement is automatic. Do not re-implement this.

---

## Common Pitfalls

### Pitfall 1: Circular Import with SlowAPI Limiter

**What goes wrong:** Defining `limiter` in `app/main.py` then importing it in routers (`from app.main import limiter`) while `app/main.py` already imports the routers. Python raises `ImportError: cannot import name 'limiter' from partially initialized module 'app.main'`.

**Why it happens:** Python's import system encounters a circular dependency at module initialization time.

**How to avoid:** Create `app/core/limiter.py` as the singleton location. Both `app/main.py` and routers import from `app/core/limiter`. The test conftest also imports from `app/core/limiter`.

**Warning signs:** `ImportError` or `AttributeError: module 'app.main' has no attribute 'limiter'` at test startup.

### Pitfall 2: SlowAPI Breaks Existing Tests (RateLimitExceeded)

**What goes wrong:** After adding SlowAPI, the 79 existing tests that call `POST /auth/login` rapidly hit the 5/minute limit and start returning 429. Tests fail with unexpected status codes.

**Why it happens:** Tests use the same `TestClient` which processes requests through the real app including the limiter. The in-memory backend does not reset between test calls.

**How to avoid:** The `disable_rate_limiter` fixture in `conftest.py` sets `limiter.enabled = False` with `autouse=True`. This disables rate limiting for ALL tests without touching existing test files.

**Warning signs:** `assert response.status_code == 200` failures showing `429` after adding SlowAPI.

### Pitfall 3: Admin Route Shows Blank for Non-Admin Instead of Redirect

**What goes wrong:** A `manager` user navigates to `/audit` — the component renders but the API call returns 403, leaving the page blank with an error state instead of redirecting.

**Why it happens:** Route guard only checks `isAuthenticated`, not `role`. The 403 is caught by the component's error handler, not the router.

**How to avoid:** Use a dedicated `RequireAdmin` guard in `App.tsx` that checks `role !== 'admin'` and navigates to `/dashboard`. This means non-admin users never reach the component at all.

### Pitfall 4: Vitest CSS Import Failures

**What goes wrong:** `import '../components/StatusBadge.css'` inside a component causes Vitest to throw `SyntaxError: Unexpected token '<'` (treating CSS as JS) or `Error: Failed to resolve import`.

**Why it happens:** Vitest's jsdom environment doesn't handle CSS files by default.

**How to avoid:** Set `css: false` in the vitest config `test` block. This tells Vitest to ignore CSS imports during tests. [ASSUMED — standard workaround; applies because several existing components import CSS files directly]

### Pitfall 5: `useNavigate` Outside Router in Tests

**What goes wrong:** Tests for `LoginPage`, `DashboardPage`, or any page that calls `useNavigate()` throw `Error: useNavigate() may be used only in the context of a <Router> component`.

**Why it happens:** `useNavigate` is a React Router hook that requires a Router context.

**How to avoid:** Wrap every component render call in tests with `<MemoryRouter>`. Use `<MemoryRouter initialEntries={['/login']}>` when the initial route matters.

### Pitfall 6: Missing `User` and `AuditLog` Types in types.ts

**What goes wrong:** `UserManagementPage.tsx` and `AuditPage.tsx` try to import types that don't exist in `types.ts`. TypeScript compilation fails.

**Why it happens:** `types.ts` currently defines `RequestSummary`, `RequestDetail`, `AIReview`, etc. but has no `User` or `AuditLog` types.

**How to avoid:** Add `User`, `UserCreate`, and `AuditLog` interfaces to `types.ts` as the first task in the frontend wave. These must match the backend `UserResponse` and `AuditLogResponse` Pydantic schemas exactly.

### Pitfall 7: GET /users/ Returns Seeded Test Users But No Department

**What goes wrong:** `UserResponse.department_id` is `Optional[int]`. The frontend must handle `null` gracefully — display "—" instead of crashing on `dept.id`.

**Why it happens:** Users can be created without a department (the `department_id` field is `Optional[int]` in both `UserCreate` and `UserResponse`).

**How to avoid:** In `UserManagementPage.tsx`, render `{user.department_id ?? '—'}` for the department column.

---

## Code Examples

### Complete SlowAPI Setup

```python
# app/core/limiter.py (NEW)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

```python
# app/main.py (MODIFIED — add these lines)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# app/routers/auth.py (MODIFIED)
from fastapi import Request
from app.core.limiter import limiter

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    ...
```

```python
# app/routers/requests.py (MODIFIED)
from fastapi import Request
from app.core.limiter import limiter

@router.post("/", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_request(request: Request, body: PurchaseRequestCreate, ...):
    ...
```

```python
# tests/conftest.py (ADD ONLY — do NOT modify existing fixtures)
from app.core.limiter import limiter

@pytest.fixture(autouse=True)
def disable_rate_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True
```

### AuditPage.tsx Template (follows DashboardPage.tsx pattern)

```tsx
// Minimal structure — planner fills detail
import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'
import type { AuditLog } from '../types'

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiClient.get<AuditLog[]>('/audit/')
      .then(r => setLogs(r.data))
      .catch(() => setError('Failed to load audit log.'))
      .finally(() => setLoading(false))
  }, [])

  // render table with columns: Time | Action | Actor | Status Change | Note
}
```

### Vitest Test for StatusBadge (pure unit — no mocking needed)

```tsx
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../components/StatusBadge'

describe('StatusBadge', () => {
  it('renders approved status with correct label', () => {
    render(<StatusBadge status="approved" />)
    expect(screen.getByText('Approved')).toBeInTheDocument()
    expect(screen.getByLabelText('Status: Approved')).toBeInTheDocument()
  })

  it('renders all 7 status values without crashing', () => {
    const statuses: Array<Parameters<typeof StatusBadge>[0]['status']> = [
      'draft', 'pending_review', 'pending_approval', 'needs_rule',
      'approved', 'rejected', 'needs_more_info'
    ]
    statuses.forEach(status => {
      const { unmount } = render(<StatusBadge status={status} />)
      expect(screen.getByRole('generic')).toBeInTheDocument()
      unmount()
    })
  })
})
```

### Vitest Test for useAuth Hook

```tsx
import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useAuth } from '../hooks/useAuth'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('starts unauthenticated when no token in localStorage', () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.role).toBeNull()
  })

  it('sets authenticated state after login', async () => {
    // JWT with role=requester (header.payload.sig)
    const fakeToken = `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.${btoa(JSON.stringify({ role: 'requester', user_id: 1, exp: 9999999999 }))}.sig`
    vi.mocked(authApi.login).mockResolvedValue({ access_token: fakeToken, token_type: 'bearer' })

    const { result } = renderHook(() => useAuth())
    await act(async () => {
      await result.current.login('alice@test.com', 'alice123')
    })
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.role).toBe('requester')
  })

  it('clears state on logout', async () => {
    localStorage.setItem('access_token', 'sometoken')
    const { result } = renderHook(() => useAuth())
    act(() => { result.current.logout() })
    expect(result.current.isAuthenticated).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flask-Limiter (Flask only) | SlowAPI (Starlette/FastAPI port) | ~2020 | Same decorator API, works with FastAPI dependency injection |
| `@testing-library/react` v12 with CRA | Vitest + RTL v16 with Vite | 2023-2025 | No Jest config needed; uses vite.config.ts; faster HMR in watch mode |
| `fireEvent` for interactions | `userEvent` (async) | v14+ | Realistic event sequences; async/await required |
| `act()` manual wrapping | `waitFor`, `findBy*` queries | RTL v13+ | Cleaner async assertions without manual act() wrapping |

**Deprecated/outdated:**
- `enzyme`: No longer maintained for React 18. Do not use.
- `@testing-library/react` < v13: React 18 incompatible.
- `MSW` (Mock Service Worker): Decision D-09 explicitly rules this out — use `vi.mock('axios')` instead.
- `limiter = Limiter(enabled=False)` in main.py: Would disable globally. Use `limiter.enabled = False` in fixture for per-session control.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `limiter.enabled = False` is the correct test override mechanism for SlowAPI 0.1.9 | Architecture Patterns / Pitfalls | Existing tests break with 429 errors after SlowAPI is added; alternative: set very high limit string or use `exempt_when` |
| A2 | Placing `limiter` singleton in `app/core/limiter.py` avoids circular import | Architecture Patterns | If FastAPI's DI system requires the limiter to be on the `app` object before router import, may need different pattern |
| A3 | `css: false` in vitest config prevents CSS import parse errors | Pitfalls | Tests may still fail on CSS; alternative is `moduleNameMapper` for `.css` files |
| A4 | `@testing-library/user-event` v14 works with `vitest` v4 and `@testing-library/react` v16 | Standard Stack | Version mismatch could require specific version pinning |
| A5 | Frontend `useAuth` hook's `parseRole` using `atob(token.split('.')[1])` works in jsdom | Code Examples | jsdom `atob` implementation may differ; test may need `global.atob` mock if it fails |

---

## Open Questions

1. **SlowAPI `request: Request` parameter position**
   - What we know: SlowAPI requires `request: Request` in the function signature
   - What's unclear: Whether it must be the first parameter or just present anywhere. Current `auth.py` uses positional-style FastAPI deps — adding `Request` first changes the function signature.
   - Recommendation: Make `request: Request` the first parameter before `body` and `db`. FastAPI resolves it automatically from the ASGI scope.

2. **Screenshot capture process**
   - What we know: Decision D-14 requires 5 PNG screenshots in `docs/screenshots/`
   - What's unclear: Whether screenshots are generated manually (browser screenshot) or automated. No screen capture tool specified.
   - Recommendation: Plan a manual capture step — the plan should list which URL to visit and what state to capture; screenshots are committed as binary files. This is a human step, not an automated task.

3. **Frontend `tsconfig.json` — `types` field**
   - What we know: Vitest globals (`describe`, `it`, `vi`) need to be declared for TypeScript
   - What's unclear: Whether the existing `tsconfig.json` already references `vitest/globals` or if a separate `tsconfig.test.json` is needed
   - Recommendation: Check `tsconfig.json` in Wave 0; add `"types": ["vitest/globals"]` if not already present, or rely on explicit imports in test files.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vitest, frontend tests | Yes | v22.12.0 | — |
| npm | Package install | Yes | bundled with Node | — |
| Python (py) | SlowAPI install, pytest | Yes | 3.12+ (3.13.13 in env) | — |
| slowapi PyPI package | Rate limiting | Not yet installed | 0.1.9 available | — |
| vitest npm package | Frontend tests | Not yet installed | 4.1.8 available | — |
| @testing-library/* | Frontend tests | Not yet installed | All confirmed available | — |
| jsdom | Frontend tests | Not yet installed | 29.1.1 available | — |

**Missing dependencies with no fallback:** None — all are installable from public registries.

**Missing dependencies with fallback:** None applicable — all packages are confirmed available and cost-free.

---

## Validation Architecture

### Test Framework (Backend — existing)

| Property | Value |
|----------|-------|
| Framework | pytest + httpx |
| Config file | none — runs from project root |
| Quick run command | `py -m pytest -x -q` |
| Full suite command | `py -m pytest --cov=app --cov-report=term-missing` |

### Test Framework (Frontend — NEW)

| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.8 + React Testing Library 16.3.2 |
| Config file | `frontend/vite.config.ts` (add `test` block) |
| Quick run command | `npm run test` (from `frontend/`) |
| Full suite command | `npm run test -- --coverage` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FR-USERS-3 | Admin create user → 201, duplicate → 400 | Backend unit | `py -m pytest tests/ -k "user" -x` | Partial (POST exists, GET /users/ missing) |
| FR-AUDIT-4 | Admin gets audit log list | Backend unit | `py -m pytest tests/ -k "audit" -x` | Likely yes (existing tests cover audit) |
| FR-FE-5 | Role-aware rendering | Frontend unit | `npm run test` | Wave 0 gap |
| NFR-SEC-3 | Rate limit on /auth/login + /requests/ | Backend unit | `py -m pytest tests/ -x` (with limiter disabled fixture) | Wave 0 gap |
| NFR-TEST-1 | Frontend testing competence demo | Frontend unit | `npm run test` | Wave 0 gap — all 5-6 files are new |
| D-08 | useAuth hook behavior | Frontend hook test | `npm run test -- useAuth` | Wave 0 gap |
| D-08 | StatusBadge renders correctly | Frontend unit | `npm run test -- StatusBadge` | Wave 0 gap |
| D-08 | ApprovalActions role-gating | Frontend unit | `npm run test -- ApprovalActions` | Wave 0 gap |
| D-08 | AIReviewPanel run analysis flow | Frontend unit | `npm run test -- AIReviewPanel` | Wave 0 gap |
| D-08 | LoginPage form submit + error | Frontend unit | `npm run test -- LoginPage` | Wave 0 gap |
| D-08 | AuditPage/DashboardPage with mock data | Frontend unit | `npm run test -- AuditPage` | Wave 0 gap |

### Sampling Rate

- **Per task commit (backend):** `py -m pytest -x -q`
- **Per task commit (frontend):** `npm run test` (from `frontend/`)
- **Per wave merge:** `py -m pytest --cov=app` + `npm run test -- --coverage`
- **Phase gate:** Both suites green before `/gsd:verify-work`

### Wave 0 Gaps (Frontend)

- [ ] `frontend/src/setup.ts` — global jest-dom matchers setup
- [ ] `frontend/src/__tests__/useAuth.test.ts` — hook tests
- [ ] `frontend/src/__tests__/StatusBadge.test.tsx` — pure unit
- [ ] `frontend/src/__tests__/ApprovalActions.test.tsx` — role-gating
- [ ] `frontend/src/__tests__/AIReviewPanel.test.tsx` — async flow
- [ ] `frontend/src/__tests__/LoginPage.test.tsx` — form submit
- [ ] `frontend/src/__tests__/AuditPage.test.tsx` — mock API data
- [ ] `frontend/vite.config.ts` — add `test` block
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`

### Wave 0 Gaps (Backend)

- [ ] `app/core/limiter.py` — SlowAPI singleton
- [ ] `GET /users/` endpoint in `app/routers/users.py`
- [ ] SlowAPI fixtures in `tests/conftest.py` (`disable_rate_limiter`)

*(Existing test infrastructure covers all other backend requirements — no additional backend test files needed for this phase.)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | JWT (existing); rate limiting on POST /auth/login (new) |
| V3 Session Management | Yes | JWT stored in localStorage (existing) |
| V4 Access Control | Yes | require_role("admin") dependency for new endpoints |
| V5 Input Validation | Yes | Pydantic v2 on all backend endpoints (existing) |
| V6 Cryptography | No | bcrypt via direct API (existing — no changes) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Brute-force login | Tampering | SlowAPI 5/min per IP on POST /auth/login |
| Spam request submission | Denial of Service | SlowAPI 20/min per IP on POST /requests/ |
| IDOR on /users/{id} | Information Disclosure | require_role("admin") — only admins access user list/update |
| Mass assignment on user create | Tampering | UserCreate schema excludes `is_active`, `hashed_password`, `id` from client input |
| Admin page access by non-admin | Elevation of Privilege | RequireAdmin guard in App.tsx + require_role in API |

**OWASP checklist items this phase closes:**
- `Rate limiting before deployment` — SlowAPI on auth + requests
- `IDOR/BOLA checks` — GET /users/ is admin-only; no individual user data exposed without admin role

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on This Phase |
|-----------|---------------------|
| Use `py` not `python` | All backend commands: `py -m pip install slowapi`, `py -m pytest` |
| Use `py -m pip`, `py -m pytest`, `py -m uvicorn` | All plan task commands must use this form |
| No paid APIs | SlowAPI and all test libraries are free/OSS — compliant |
| No random dependencies | Each package justified: slowapi (rate limiting), vitest+RTL (testing) |
| No one-file app | New files: `app/core/limiter.py`, `AuditPage.tsx`, `UserManagementPage.tsx`, `frontend/src/api/users.ts`, `frontend/src/api/audit.ts` — all properly modularized |
| Humans approve/reject (AI advisory only) | No change to AI boundary in this phase |
| Every sensitive status change must create audit log | No new status changes introduced in this phase; existing audit service unchanged |
| Protect against IDOR/BOLA | New GET /users/ endpoint uses `require_role("admin")` — no user-scoped access to other users |
| No mass assignment | UserCreate/UserAdminUpdate schemas already enforce separation |
| Never commit secrets | `.env.example` unchanged; no new secrets introduced |
| Windows development | npm commands run as-is; `py -m pip install slowapi` |
| No autonomous spending approval | Not applicable to this phase |

---

## Sources

### Primary (HIGH confidence)

- PyPI registry — `pip index versions slowapi` — confirmed 0.1.9, 10 versions history
- npm registry — `npm view vitest/react-testing-library/jsdom version` — all confirmed current
- Codebase direct reads — `app/main.py`, `app/routers/*.py`, `tests/conftest.py`, `frontend/src/**` — all read in this session

### Secondary (MEDIUM confidence)

- SlowAPI docs (slowapi.readthedocs.io) — integration pattern for main.py, decorator order requirement
- SlowAPI GitHub docs/examples.md — `limiter.enabled = False` documented test approach [CITED: github.com/laurentS/slowapi/blob/master/docs/examples.md]
- PyPI project page (pypi.org/project/slowapi/) — confirmed maintainer, GitHub repo, MIT license

### Tertiary (LOW confidence)

- `css: false` vitest config pattern — from training knowledge; standard solution for CSS import issues in Vitest [ASSUMED]
- Circular import avoidance pattern — standard Python practice, applied to this codebase based on `app/main.py` structure [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on npm/PyPI registries with current versions
- Architecture: HIGH — based on direct codebase reads of all referenced files
- SlowAPI integration: MEDIUM-HIGH — decorator pattern and limiter.enabled from official docs; circular import solution is assumed
- Frontend test patterns: MEDIUM — Vitest + RTL is well-documented; specific CSS handling and hook test patterns are assumed based on training knowledge
- Pitfalls: HIGH — derived from actual codebase structure (circular imports are a real risk given current main.py layout)

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (packages stable; SlowAPI moves slowly)
