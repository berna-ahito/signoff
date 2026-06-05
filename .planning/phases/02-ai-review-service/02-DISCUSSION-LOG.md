# Phase 2: AI Review Service - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 2-AI Review Service
**Areas discussed:** Execution order, AIReview persistence design, Groq reliability boundary, Slack trigger scope

---

## Execution Order

| Option | Description | Selected |
|--------|-------------|----------|
| ABC → config → ORM | Write service once. Provider interface first, persistence integrates cleanly. | ✓ |
| ORM first | Persist with MockProvider, refactor when adding ABC. Two touches to service layer. | |
| You decide | Claude picks best order. | |

**User's choice:** ABC → config → ORM (Recommended)
**Notes:** Dependency-driven order wins. Avoids rewriting `generate_ai_review()` twice.

---

| Option | Description | Selected |
|--------|-------------|----------|
| app/core/deps.py | Already contains FastAPI DI helpers. No new file. | ✓ |
| app/routers/utils.py | New router-scoped file. One function per file. | |
| You decide | Claude picks. | |

**User's choice:** app/core/deps.py
**Notes:** `_get_request_or_403` moves to existing deps.py. Both routers update their imports.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Move to sub-package app/services/ai_review/ | Matches ROADMAP.md deliverables spec. | |
| Keep flat in app/services/ | Less disruption. Simpler imports. | ✓ |

**User's choice:** Keep flat in app/services/
**Notes:** ROADMAP sub-package layout overridden. All provider files stay flat.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Commit current state first | Clean baseline. Phase 2 regressions are clearly Phase 2. | ✓ |
| Fold into first Phase 2 commit | Fewer commits. | |

**User's choice:** Commit current state first
**Notes:** Two modified files (ai_reviews.py, approval_engine.py) committed before Phase 2 work begins.

---

## AIReview Persistence Design

| Option | Description | Selected |
|--------|-------------|----------|
| Return cached result | Cache by (request_id, provider_name). No re-run. | ✓ |
| Always re-run | Fresh AI call every time. Groq hits rate limits. | |
| Re-run and overwrite | Replace stored row. Blurs audit trail. | |

**User's choice:** Return cached result (Recommended)
**Notes:** Cache key = (request_id, provider_name). Critical for Groq rate limit management.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — embed in request detail | GET /requests/{id} returns nullable ai_review field. One call for frontend. | ✓ |
| No — separate endpoint only | GET stays clean; frontend calls separately. | |

**User's choice:** Yes — embed in request detail (Recommended)
**Notes:** Nullable `ai_review: AIReviewResult | None` field in `PurchaseRequestDetail` response schema.

---

| Option | Description | Selected |
|--------|-------------|----------|
| JSON column + Text | SQLAlchemy JSON type for missing_info. Text for rfq_draft. Simple. | ✓ |
| Normalize into separate table | missing_info rows. Over-engineered. | |
| You decide | Claude picks. | |

**User's choice:** JSON column for list fields, Text for rfq_draft (Recommended)

---

## Groq Reliability Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Raise HTTP 502 Bad Gateway | Hard error on Pydantic validation failure. | |
| Silent fallback to MockProvider | Transparent recovery. Log warning. | ✓ |
| Log and return partial result | Fill what we can. Risky with Literal fields. | |

**User's choice:** Silent fallback to MockProvider
**Notes:** Catch `ValidationError` + `groq.APIError`. Log warning. Fall back to `MockAIProvider().review(request)`.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Always Mock in tests | PROCUREFLOW_AI_PROVIDER=mock in conftest.py. Offline, deterministic. | ✓ |
| Optional integration tests | @pytest.mark.groq, skip unless GROQ_API_KEY set. | |

**User's choice:** Always Mock in tests (Recommended)
**Notes:** monkeypatch.setenv or conftest fixture forces mock provider in all test runs.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in GroqProvider class | Prompt in groq_provider.py. Easy to iterate. | ✓ |
| External template file | .txt or .jinja2. Adds file dependency. | |

**User's choice:** Inline in GroqProvider class (Recommended)

---

## Slack Trigger Scope

| Option | Description | Selected |
|--------|-------------|----------|
| AI flags high-risk | risk_level="high" in AIReviewResult | ✓ |
| Request approved | ApprovalDecision decision="approved" | ✓ |
| Request rejected | ApprovalDecision decision="rejected" | ✓ |
| Request needs_more_info | Status transition to needs_more_info | |

**User's choice:** High-risk AI flag + approved + rejected
**Notes:** Three events. needs_more_info excluded — different UX flow, deferred.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Silent skip — log warning | SLACK_WEBHOOK_URL optional. App works without it. | ✓ |
| Fail at startup | Strict. Makes local dev harder. | |

**User's choice:** Silent skip — log warning (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Inside service layer | ai_review_service.py and approval_engine.py call notify. | ✓ |
| In router layer | Router calls notify after service returns. | |

**User's choice:** Inside service layer (Recommended)
**Notes:** Consistent pattern: both services own their notifications.

---

## Claude's Discretion

- Groq prompt wording (must enumerate valid Literal values explicitly)
- `AIReview` ORM column names (follow existing models.py snake_case conventions)
- Slack message format (plain text: request ID, title, status/risk, no SDK needed)

## Deferred Ideas

- Groq integration tests with real API key (`@pytest.mark.groq`) — Phase 5
- Cache invalidation on request edit (stale review after data change) — Phase 5
- `needs_more_info` Slack notification — Phase 4/5
