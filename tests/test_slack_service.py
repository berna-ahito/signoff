from unittest.mock import MagicMock, patch

import app.services.slack_service as slack_module
from app.services.slack_service import notify_slack


def test_no_op_when_url_unset(monkeypatch):
    monkeypatch.setattr(slack_module.settings, "slack_webhook_url", "")
    with patch("app.services.slack_service.httpx.post") as mock_post:
        notify_slack("TEST", 1, "Title", "detail")
    mock_post.assert_not_called()


def test_posts_when_url_set(monkeypatch):
    monkeypatch.setattr(slack_module.settings, "slack_webhook_url", "https://hooks.slack.com/fake")
    with patch("app.services.slack_service.httpx.post") as mock_post:
        notify_slack("APPROVED", 42, "Server Purchase", "note=none")
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    url_arg = call_kwargs[0][0] if call_kwargs[0] else call_kwargs[1].get("url")
    assert "hooks.slack.com" in url_arg
    payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
    assert "APPROVED" in payload["text"]
    assert "42" in payload["text"]


def test_swallows_httpx_exception(monkeypatch):
    monkeypatch.setattr(slack_module.settings, "slack_webhook_url", "https://hooks.slack.com/fake")
    with patch("app.services.slack_service.httpx.post", side_effect=Exception("timeout")):
        notify_slack("REJECTED", 7, "Laptop", "note=budget exceeded")


def test_slack_fires_on_approval_decision(db_session):
    from app.db.models import PurchaseRequest, User
    from app.core.security import get_password_hash
    from app.services.approval_engine import apply_decision

    user = User(
        email="slack_test@example.com",
        hashed_password=get_password_hash("pw"),
        full_name="Slack Tester",
        role="requester",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    req = PurchaseRequest(
        title="Test Item",
        description="Description for slack test",
        category="IT",
        urgency="low",
        quantity=1,
        estimated_cost=300.0,
        justification="Needed for project",
        status="pending_approval",
        requester_id=user.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    with patch("app.services.approval_engine.notify_slack") as mock_notify:
        apply_decision(db_session, req, "approved", "Looks good")

    mock_notify.assert_called_once_with(
        event="APPROVED",
        request_id=req.id,
        title="Test Item",
        detail="note=Looks good",
    )


def test_slack_fires_on_high_risk_review(client, seed_users, auth_headers, db_session):
    from app.services.mock_ai_provider import MockAIProvider
    from app.schemas.ai_review import AIReviewResult
    import app.services.ai_review_service as ai_svc

    high_risk_result = AIReviewResult(
        summary="High risk item",
        category="IT",
        urgency="high",
        risk_level="high",
        missing_info=[],
        recommended_action="finance_review",
        rfq_draft="RFQ draft text",
        confidence=0.9,
    )

    with patch.object(ai_svc._provider, "review", return_value=high_risk_result):
        with patch("app.services.ai_review_service.notify_slack") as mock_notify:
            resp = client.post("/requests/", json={
                "title": "Expensive Server",
                "description": "High value server purchase for production environment scaling",
                "category": "IT",
                "urgency": "high",
                "quantity": 1,
                "estimated_cost": 20000.0,
                "justification": "Required for production workload and system reliability at scale",
            }, headers=auth_headers["alice"])
            req_id = resp.json()["id"]
            client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])

    mock_notify.assert_called_once()
    call_kwargs = mock_notify.call_args[1]
    assert call_kwargs["event"] == "HIGH RISK"
    assert call_kwargs["request_id"] == req_id
