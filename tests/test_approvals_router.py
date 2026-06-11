import pytest
from app.db.models import PurchaseRequest


def _make_pending(db_session, owner_id: int) -> int:
    req = PurchaseRequest(
        title="Test request",
        description="Test",
        category="IT",
        urgency="medium",
        quantity=1,
        estimated_cost=500.0,
        justification="Test",
        status="pending_approval",
        assigned_role="manager",
        requester_id=owner_id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    return req.id


def test_requester_cannot_approve_own_request(client, seed_users, auth_headers, db_session):
    req_id = _make_pending(db_session, seed_users["alice"].id)
    resp = client.post(
        f"/approvals/{req_id}/decide",
        json={"decision": "approved", "note": "LGTM"},
        headers=auth_headers["alice"],
    )
    assert resp.status_code == 403


def test_double_approve_returns_400(client, seed_users, auth_headers, db_session):
    req_id = _make_pending(db_session, seed_users["alice"].id)

    first = client.post(
        f"/approvals/{req_id}/decide",
        json={"decision": "approved", "note": "LGTM"},
        headers=auth_headers["bob"],
    )
    assert first.status_code == 200

    second = client.post(
        f"/approvals/{req_id}/decide",
        json={"decision": "approved", "note": "Again"},
        headers=auth_headers["bob"],
    )
    assert second.status_code == 400
