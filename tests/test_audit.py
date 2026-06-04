import pytest
from app.db.models import ApprovalRule, AuditLog


def _add_rules(db):
    rules = [
        ApprovalRule(name="Low Value", min_amount=0, max_amount=999.99, category=None, required_role="manager", priority=10, is_active=True),
    ]
    db.add_all(rules)
    db.commit()


def _create_and_submit(client, headers):
    resp = client.post("/requests/", json={
        "title": "Audit Test Request",
        "description": "Request to test audit log creation",
        "category": "IT", "urgency": "medium", "quantity": 1,
        "estimated_cost": 500.0,
        "justification": "Audit test justification text here"
    }, headers=headers)
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=headers)
    return req_id


def test_submit_creates_audit_log(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit(client, auth_headers["alice"])
    logs = db_session.query(AuditLog).filter(AuditLog.request_id == req_id).all()
    assert len(logs) >= 1
    actions = [log.action for log in logs]
    assert any("submitted" in a or "routed" in a for a in actions)


def test_approval_decision_creates_audit_log(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit(client, auth_headers["alice"])
    # Bob is manager — approve the request
    client.post(
        f"/approvals/{req_id}/decide",
        json={"decision": "approved", "note": "Looks good"},
        headers=auth_headers["bob"],
    )
    logs = db_session.query(AuditLog).filter(AuditLog.request_id == req_id).all()
    assert len(logs) >= 2
    new_statuses = [log.new_status for log in logs]
    assert "approved" in new_statuses


def test_audit_log_is_read_only_via_api(client, seed_users, auth_headers):
    resp = client.get("/openapi.json")
    paths = resp.json()["paths"]
    audit_paths = {k: v for k, v in paths.items() if "/audit" in k}
    for path, methods in audit_paths.items():
        assert "post" not in methods, f"Unexpected POST on audit path {path}"
        assert "patch" not in methods, f"Unexpected PATCH on audit path {path}"
        assert "delete" not in methods, f"Unexpected DELETE on audit path {path}"


def test_admin_can_read_audit_for_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit(client, auth_headers["alice"])
    resp = client.get(f"/audit/requests/{req_id}", headers=auth_headers["admin"])
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_non_admin_cannot_read_audit(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit(client, auth_headers["alice"])
    resp = client.get(f"/audit/requests/{req_id}", headers=auth_headers["alice"])
    assert resp.status_code == 403
