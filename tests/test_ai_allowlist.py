"""Tests for Phase 2E: AI output allowlist with service-layer sanitization."""
import pytest
from unittest.mock import patch

import app.services.ai_review_service as _ai_svc
from app.schemas.ai_review import AIReviewResult
from app.db.models import AIReview


def _base_review_result(**overrides) -> AIReviewResult:
    """Return a valid AIReviewResult, with fields overridden by kwargs before construction.

    Because AIReviewResult validates on construction we build the dict first,
    bypass the Pydantic layer using model_construct, then let the sanitizer fix it.
    We use model_construct so Pydantic doesn't reject the garbage value before
    the service sanitizer even sees it.
    """
    defaults = dict(
        summary="Test summary",
        category="IT",
        urgency="medium",
        risk_level="low",
        missing_info=[],
        recommended_action="approve",
        rfq_draft="RFQ draft text",
        confidence=0.9,
    )
    defaults.update(overrides)
    return AIReviewResult.model_construct(**defaults)


def test_garbage_risk_level_defaults_to_unknown(client, seed_users, auth_headers, db_session):
    """Provider returning an unrecognised risk_level should be stored as 'unknown'."""
    garbage = _base_review_result(risk_level="critical")

    with patch.object(_ai_svc._provider, "review", return_value=garbage):
        resp = client.post("/requests/", json={
            "title": "Garbage Risk Test",
            "description": "Need this item for important work across the whole department",
            "category": "IT",
            "urgency": "low",
            "quantity": 1,
            "estimated_cost": 200.0,
            "justification": "Required for ongoing project delivery this quarter",
        }, headers=auth_headers["alice"])
        assert resp.status_code == 201
        req_id = resp.json()["id"]

        review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
        assert review_resp.status_code == 200

    row = db_session.query(AIReview).filter_by(request_id=req_id).first()
    assert row is not None
    assert row.risk_level == "unknown", (
        f"Expected 'unknown' but got {row.risk_level!r}"
    )


def test_garbage_action_defaults_to_review(client, seed_users, auth_headers, db_session):
    """Provider returning an unrecognised recommended_action should be stored as 'review'."""
    garbage = _base_review_result(recommended_action="auto_approve")

    with patch.object(_ai_svc._provider, "review", return_value=garbage):
        resp = client.post("/requests/", json={
            "title": "Garbage Action Test",
            "description": "Need this item for important work across the whole department",
            "category": "IT",
            "urgency": "low",
            "quantity": 1,
            "estimated_cost": 200.0,
            "justification": "Required for ongoing project delivery this quarter",
        }, headers=auth_headers["alice"])
        assert resp.status_code == 201
        req_id = resp.json()["id"]

        review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
        assert review_resp.status_code == 200

    row = db_session.query(AIReview).filter_by(request_id=req_id).first()
    assert row is not None
    assert row.recommended_action == "review", (
        f"Expected 'review' but got {row.recommended_action!r}"
    )
