import pytest
from sqlalchemy.orm import Session

from app.db.models import ApprovalRule


def _add_rules(db: Session):
    rules = [
        ApprovalRule(name="Low Value", min_amount=0, max_amount=999.99, category=None, required_role="manager", priority=10, is_active=True),
        ApprovalRule(name="High Value", min_amount=1000, max_amount=None, category=None, required_role="finance", priority=20, is_active=True),
    ]
    db.add_all(rules)
    db.commit()


def _create_request(client, headers, overrides=None):
    body = {
        "title": "Test Laptop",
        "description": "Need a laptop for development work",
        "category": "IT",
        "urgency": "high",
        "quantity": 1,
        "estimated_cost": 800.0,
        "justification": "Current machine is too slow for builds",
    }
    if overrides:
        body.update(overrides)
    return client.post("/requests/", json=body, headers=headers)


def test_requester_can_create_request(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["requester_id"] == seed_users["alice"].id


def test_request_status_defaults_to_draft(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    assert resp.json()["status"] == "draft"


def test_submit_request_changes_status(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    submit_resp = client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    assert submit_resp.status_code == 200
    new_status = submit_resp.json()["status"]
    assert new_status in ("pending_approval", "needs_rule")


def test_submit_requires_draft_status(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    # Submit again
    second = client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    assert second.status_code == 400


def test_requester_can_see_own_requests(client, seed_users, auth_headers):
    _create_request(client, auth_headers["alice"])
    resp = client.get("/requests/", headers=auth_headers["alice"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_manager_can_see_routed_requests(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    bob_resp = client.get("/requests/", headers=auth_headers["bob"])
    assert bob_resp.status_code == 200


def test_invalid_request_body_returns_422(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"], overrides={"quantity": -1})
    assert resp.status_code == 422


def test_estimated_cost_must_be_positive(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"], overrides={"estimated_cost": 0})
    assert resp.status_code == 422


def test_non_requester_cannot_create_request(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["bob"])
    assert resp.status_code == 403
