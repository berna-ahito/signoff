# Phase 2: AI Review Service - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the provider-agnostic AI review layer: abstract provider interface (ABC), config-driven provider selection, AIReview persistence in DB, Groq integration (free tier, llama-3.1-8b-instant), and optional Slack webhook notifications. MockProvider remains the default. No frontend changes.

</domain>

<decisions>
## Implementation Decisions

### Execution Order (locked)
- **D-01:** Commit current uncommitted state (`ai_reviews.py`, `approval_engine.py`) as a clean baseline before any Phase 2 work begins.
- **D-02:** Move `_get_request_or_403` to `app/core/deps.py` (first task). Update both `requests.py` and `ai_reviews.py` imports.
- **D-03:** Implement ABC (`AIReviewProvider` base class in `app/services/ai_review_base.py`) before config selection or Groq.
- **D-04:** Implement config-driven provider selection (env var `PROCUREFLOW_AI_PROVIDER=mock|groq`) after ABC exists.
- **D-05:** Add `AIReview` ORM model + Alembic migration after provider layer is stable (ABC + config done).
- **D-06:** Implement Groq provider (`app/services/groq_provider.py`) after ORM exists.
- **D-07:** Add Slack webhook notifications last (optional, best-effort).
- **D-08:** Keep provider files flat in `app/services/` — do NOT create `ai_review/` sub-package.

### AIReview Persistence
- **D-09:** Cache by `(request_id, provider_name)`. If an `ai_reviews` row exists for this pair, return it without re-running the provider. Groq is rate-limited — no redundant calls.
- **D-10:** `GET /requests/{id}` returns embedded AI review (nullable) in the response body. Frontend gets everything in one call. Matches Phase 3 detail view requirements.
- **D-11:** Store `missing_info` as a JSON column (SQLAlchemy `JSON` type, stored as TEXT in SQLite). Store `rfq_draft` as `Text`. No join tables.

### Groq Reliability Boundary
- **D-12:** If Groq returns malformed JSON or fields that fail `AIReviewResult` Pydantic validation, **silently fall back to MockProvider**. Log the failure with `logging.warning()`. No hard error exposed to caller.
- **D-13:** Tests NEVER hit real Groq. `PROCUREFLOW_AI_PROVIDER=mock` forced in `conftest.py` (via `monkeypatch.setenv` or fixture). Groq provider only activates at runtime when explicitly configured.
- **D-14:** Prompt template lives inline in `GroqProvider` class — no external template files.

### Slack Notifications
- **D-15:** Three events fire the Slack webhook: AI flags `risk_level="high"`, request `approved`, request `rejected`.
- **D-16:** If `SLACK_WEBHOOK_URL` is not set, silently skip — log `logging.warning("SLACK_WEBHOOK_URL not set, skipping notification")` and continue. Slack is optional; app works without it.
- **D-17:** Slack notification calls live inside the **service layer**: `ai_review_service.py` notifies after storing a high-risk result; `approval_engine.py` notifies after `apply_decision` for approved/rejected.

### Claude's Discretion
- Groq JSON mode prompt engineering: structure the prompt to enumerate valid Literal values explicitly. Claude has flexibility on exact wording.
- `AIReview` ORM column names: follow existing `models.py` conventions (snake_case, `created_at` timestamp).
- Slack message format: plain text, include request ID, title, status/risk level, and a link-ready request ID. Claude picks format.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Foundation
- `.planning/ROADMAP.md` — Phase 2 deliverables spec (note: keep flat `app/services/` structure, ignore sub-package layout in ROADMAP)
- `.planning/PROJECT.md` — Product constraints (free APIs only, no paid services, humans approve/reject)
- `.planning/REQUIREMENTS.md` — Overall requirements

### Existing Code (read before writing anything)
- `app/schemas/ai_review.py` — `AIReviewResult` schema with Literal constraints. Any provider output MUST satisfy this schema.
- `app/services/mock_ai_provider.py` — `MockAIProvider.review()` — the reference implementation. ABC must be backward-compatible with this signature.
- `app/services/ai_review_service.py` — current service (module-level singleton `_provider`) — will be refactored to support config-driven selection.
- `app/routers/ai_reviews.py` — current router. Imports `_get_request_or_403` from `requests.py` — this is the import smell to fix first.
- `app/routers/requests.py` — contains `_get_request_or_403` (source of truth until moved).
- `app/core/deps.py` — destination for `_get_request_or_403` after move.
- `app/db/models.py` — existing ORM models. `AIReview` model goes here. Follow existing Column/DateTime patterns.
- `app/core/config.py` — `Settings` (pydantic-settings BaseSettings). Add `AI_PROVIDER: str = "mock"` and `GROQ_API_KEY: str = ""` and `SLACK_WEBHOOK_URL: str = ""` here.

### Test Files (do not break)
- `tests/` — 64 tests must stay green throughout every change. Run `py -m pytest` after each commit.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_get_request_or_403(db, request_id, current_user)` in `requests.py:L1` — moving to `deps.py`. Both routers use it.
- `Settings` singleton in `app/core/config.py` — add new env vars here. Already uses `pydantic-settings` BaseSettings with fail-fast pattern.
- `AuditLog` model — already has `action`, `old_status`, `new_status` columns. Slack notifications can read from the same events that write audit logs.

### Established Patterns
- **Module-level singletons:** `_provider = MockAIProvider()` in service — extend to `_provider = _load_provider()` factory function based on settings.
- **Classical Column mapping:** All ORM models use `Column(Type, ...)` not `mapped_column`. `AIReview` model must follow this.
- **`_now()` default:** All `created_at` columns use `default=_now` function. Use same pattern.
- **Pydantic validation at schema boundary:** `AIReviewResult` is the contract. Groq output must be parsed through it — Pydantic `model_validate()` catches Literal mismatches.

### Integration Points
- `POST /requests/{id}/ai-review` → `generate_ai_review()` → provider → store result → return `AIReviewResult`
- `GET /requests/{id}` → `PurchaseRequestDetail` schema needs an optional `ai_review: AIReviewResult | None` field
- `apply_decision()` in `approval_engine.py` → after commit, call `notify_slack()` for approved/rejected
- `generate_ai_review()` in `ai_review_service.py` → after store, call `notify_slack()` if `risk_level == "high"`

</code_context>

<specifics>
## Specific Ideas

- Groq model: `llama-3.1-8b-instant` (free tier). Use `groq` Python SDK (not raw HTTP).
- Provider env var: `PROCUREFLOW_AI_PROVIDER=mock` (default) or `groq`.
- Groq fallback: catch `ValidationError` from Pydantic and any `groq.APIError`, log warning, fall back to `MockAIProvider().review(request)`.
- `AIReview` ORM table name: `ai_reviews`. Columns: `id`, `request_id` (FK), `provider_name` (str), `summary`, `category`, `urgency`, `risk_level`, `missing_info` (JSON), `recommended_action`, `rfq_draft` (Text), `confidence` (Float), `created_at`.
- Slack payload: use `httpx.post()` (already in requirements.txt) with JSON body `{"text": "..."}` — no Slack SDK needed.

</specifics>

<deferred>
## Deferred Ideas

- **Groq integration tests with real API key** — marked `@pytest.mark.groq`, skip unless `GROQ_API_KEY` set. Out of scope for Phase 2; could be added in Phase 5 (integration tests).
- **Re-run AI review after request edit** — if request data changes, cached review may be stale. Cache invalidation on update is a Phase 5 concern.
- **needs_more_info Slack notification** — discussed, excluded from Phase 2. Requester notification is a different UX flow. Consider for Phase 4/5.

</deferred>

---

*Phase: 2-AI Review Service*
*Context gathered: 2026-06-05*
