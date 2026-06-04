import pytest

from app.db.models import ApprovalRule, User
from app.core.security import get_password_hash


def _add_rules(db):
    rules = [
        ApprovalRule(name="Low Value", min_amount=0, max_amount=999.99, category=None, required_role="manager", priority=10, is_active=True),
        ApprovalRule(name="High Value", min_amount=1000, max_amount=None, category=None, required_role="finance", priority=20, is_active=True),
    ]
    db.add_all(rules)
    db.commit()


def _create_and_submit_request(client, headers, cost=800.0):
    body = {
        "title": "Test Request",
        "description": "Description for test request purposes",
        "category": "IT",
        "urgency": "medium",
        "quantity": 1,
        "estimated_cost": cost,
        "justification": "Justification text for this test request",
    }
    resp = client.post("/requests/", json=body, headers=headers)
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=headers)
    return req_id


def test_requester_cannot_access_other_user_request_detail(client, seed_users, auth_headers, db_session):
    # Create a second requester
    carol2 = User(email="carol2@test.com", hashed_password=get_password_hash("carol2pass"),
                  full_name="Carol Two", role="requester", is_active=True)
    db_session.add(carol2)
    db_session.commit()
    db_session.refresh(carol2)
    login = client.post("/auth/login", json={"email": "carol2@test.com", "password": "carol2pass"})
    carol2_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Alice creates request
    resp = client.post("/requests/", json={
        "title": "Alice Request", "description": "Alice needs something here",
        "category": "IT", "urgency": "low", "quantity": 1,
        "estimated_cost": 100.0, "justification": "Alice justification text here"
    }, headers=auth_headers["alice"])
    req_id = resp.json()["id"]

    # carol2 tries to access it
    get_resp = client.get(f"/requests/{req_id}", headers=carol2_headers)
    assert get_resp.status_code == 403


def test_requester_can_access_own_request(client, seed_users, auth_headers):
    resp = client.post("/requests/", json={
        "title": "My Request", "description": "My own request description",
        "category": "IT", "urgency": "low", "quantity": 1,
        "estimated_cost": 100.0, "justification": "My justification text here"
    }, headers=auth_headers["alice"])
    req_id = resp.json()["id"]
    get_resp = client.get(f"/requests/{req_id}", headers=auth_headers["alice"])
    assert get_resp.status_code == 200


def test_manager_can_access_assigned_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit_request(client, auth_headers["alice"], cost=800.0)
    # Low value routes to manager
    resp = client.get(f"/requests/{req_id}", headers=auth_headers["bob"])
    assert resp.status_code == 200


def test_manager_cannot_access_finance_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    req_id = _create_and_submit_request(client, auth_headers["alice"], cost=5000.0)
    # High value routes to finance — bob (manager) should get 403
    resp = client.get(f"/requests/{req_id}", headers=auth_headers["bob"])
    assert resp.status_code == 403


def test_admin_can_access_any_request(client, seed_users, auth_headers):
    resp = client.post("/requests/", json={
        "title": "Admin Test", "description": "Admin can see any request",
        "category": "IT", "urgency": "low", "quantity": 1,
        "estimated_cost": 100.0, "justification": "Justification for admin test"
    }, headers=auth_headers["alice"])
    req_id = resp.json()["id"]
    get_resp = client.get(f"/requests/{req_id}", headers=auth_headers["admin"])
    assert get_resp.status_code == 200


def test_idor_uses_403_not_404(client, seed_users, auth_headers, db_session):
    carol2 = User(email="carol2b@test.com", hashed_password=get_password_hash("carol2bpass"),
                  full_name="Carol 2B", role="requester", is_active=True)
    db_session.add(carol2)
    db_session.commit()
    db_session.refresh(carol2)
    login = client.post("/auth/login", json={"email": "carol2b@test.com", "password": "carol2bpass"})
    carol2_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.post("/requests/", json={
        "title": "Alice Priv", "description": "Private request content here",
        "category": "IT", "urgency": "low", "quantity": 1,
        "estimated_cost": 50.0, "justification": "Private justification for request"
    }, headers=auth_headers["alice"])
    req_id = resp.json()["id"]

    get_resp = client.get(f"/requests/{req_id}", headers=carol2_headers)
    assert get_resp.status_code == 403
    assert get_resp.status_code != 404
