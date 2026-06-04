import pytest

from app.core.security import get_password_hash
from app.db.models import ApprovalRule, PurchaseRequest, User
from app.services.mock_ai_provider import MockAIProvider

VALID_ACTIONS = {"request_more_info", "manager_review", "finance_review", "ready_for_rfq"}
FORBIDDEN_ACTIONS = {"approved", "approve", "rejected", "reject"}


def _add_rules(db):
    rules = [
        ApprovalRule(name="Low Value", min_amount=0, max_amount=999.99, category=None,
                     required_role="manager", priority=10, is_active=True),
        ApprovalRule(name="High Value", min_amount=1000, max_amount=None, category=None,
                     required_role="finance", priority=20, is_active=True),
    ]
    db.add_all(rules)
    db.commit()


def _create_request(client, headers, cost=500.0, desc=None, justification=None):
    body = {
        "title": "Test Laptop",
        "description": desc or "Need a laptop for development and build work, current is slow",
        "category": "IT",
        "urgency": "medium",
        "quantity": 1,
        "estimated_cost": cost,
        "justification": justification or "This is needed to complete development tasks on time",
    }
    return client.post("/requests/", json=body, headers=headers)


def _assert_valid_review(data: dict):
    assert "summary" in data
    assert data["urgency"] in ("low", "medium", "high")
    assert data["risk_level"] in ("low", "medium", "high")
    assert isinstance(data["missing_info"], list)
    assert data["recommended_action"] in VALID_ACTIONS
    assert "rfq_draft" in data
    assert 0.0 <= data["confidence"] <= 1.0


# --- Access control ---

def test_requester_can_get_ai_review_own_request(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    assert resp.status_code == 201
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
    assert review_resp.status_code == 200
    _assert_valid_review(review_resp.json())


def test_other_requester_cannot_get_ai_review(client, seed_users, auth_headers, db_session):
    eve = User(email="eve@test.com", hashed_password=get_password_hash("eve123"),
               full_name="Eve Test", role="requester", is_active=True)
    db_session.add(eve)
    db_session.commit()
    db_session.refresh(eve)
    login = client.post("/auth/login", json={"email": "eve@test.com", "password": "eve123"})
    eve_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]

    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=eve_headers)
    assert review_resp.status_code == 403


def test_unauthenticated_cannot_get_ai_review(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review")
    assert review_resp.status_code == 401


def test_manager_can_get_ai_review_assigned_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"], cost=800.0)
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["bob"])
    assert review_resp.status_code == 200


def test_manager_cannot_get_ai_review_finance_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"], cost=5000.0)
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["bob"])
    assert review_resp.status_code == 403


def test_finance_can_get_ai_review_assigned_request(client, seed_users, auth_headers, db_session):
    _add_rules(db_session)
    resp = _create_request(client, auth_headers["alice"], cost=5000.0)
    req_id = resp.json()["id"]
    client.post(f"/requests/{req_id}/submit", headers=auth_headers["alice"])
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["carol"])
    assert review_resp.status_code == 200


def test_admin_can_get_ai_review_any_request(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["admin"])
    assert review_resp.status_code == 200


# --- Missing info detection ---

def test_missing_info_detection(client, seed_users, auth_headers):
    resp = client.post("/requests/", json={
        "title": "Quick Buy",
        "description": "Short desc here",
        "category": "IT",
        "urgency": "low",
        "quantity": 1,
        "estimated_cost": 100.0,
        "justification": "Need it now",
    }, headers=auth_headers["alice"])
    assert resp.status_code == 201
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert len(data["missing_info"]) > 0
    assert "detailed description needed" in data["missing_info"]
    assert "stronger justification needed" in data["missing_info"]
    assert "vendor not specified" in data["missing_info"]


# --- Output invariants ---

def test_confidence_always_between_0_and_1(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert 0.0 <= data["confidence"] <= 1.0


def test_recommended_action_is_never_approval(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    review_resp = client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["recommended_action"] not in FORBIDDEN_ACTIONS
    assert data["recommended_action"] in VALID_ACTIONS


def test_ai_review_does_not_mutate_status(client, seed_users, auth_headers):
    resp = _create_request(client, auth_headers["alice"])
    req_id = resp.json()["id"]
    status_before = resp.json()["status"]

    client.post(f"/requests/{req_id}/ai-review", headers=auth_headers["alice"])

    get_resp = client.get(f"/requests/{req_id}", headers=auth_headers["alice"])
    assert get_resp.json()["status"] == status_before


# --- MockProvider unit tests ---

def test_mock_provider_is_deterministic():
    req = PurchaseRequest(
        id=99,
        title="Test Item",
        description="A detailed description for testing the mock AI provider behavior here",
        category="IT",
        urgency="medium",
        quantity=1,
        estimated_cost=500.0,
        justification="This justification is long enough to pass the missing info check here",
        status="draft",
        requester_id=1,
    )
    provider = MockAIProvider()
    result1 = provider.review(req)
    result2 = provider.review(req)
    assert result1 == result2
    assert result1.confidence == result2.confidence
    assert result1.recommended_action == result2.recommended_action
    assert result1.risk_level == result2.risk_level


def test_mock_provider_high_cost_routes_to_finance():
    req = PurchaseRequest(
        id=100,
        title="Expensive Server",
        description="A detailed description of the server hardware needed for our infrastructure",
        category="Infrastructure",
        urgency="high",
        quantity=1,
        estimated_cost=15000.0,
        justification="This server is required for production workload scaling and reliability",
        status="draft",
        requester_id=1,
        vendor_id=1,
    )
    provider = MockAIProvider()
    result = provider.review(req)
    assert result.risk_level == "high"
    assert result.recommended_action == "finance_review"
    assert 0.0 <= result.confidence <= 1.0


def test_mock_provider_critical_urgency_maps_to_high():
    req = PurchaseRequest(
        id=101,
        title="Emergency Parts",
        description="A detailed description of emergency parts needed for critical systems repair",
        category="Maintenance",
        urgency="critical",
        quantity=5,
        estimated_cost=200.0,
        justification="Critical system failure requires immediate replacement of these components",
        status="draft",
        requester_id=1,
        vendor_id=1,
    )
    provider = MockAIProvider()
    result = provider.review(req)
    assert result.urgency == "high"


def test_mock_provider_low_cost_complete_request_ready_for_rfq():
    req = PurchaseRequest(
        id=102,
        title="Office Supplies",
        description="A detailed description of the office supplies required for the quarterly restock",
        category="Office",
        urgency="low",
        quantity=10,
        estimated_cost=150.0,
        justification="Regular quarterly restock of essential office supplies for the team",
        status="draft",
        requester_id=1,
        vendor_id=2,
    )
    provider = MockAIProvider()
    result = provider.review(req)
    assert result.risk_level == "low"
    assert result.missing_info == []
    assert result.recommended_action == "ready_for_rfq"
    assert result.confidence == 1.0
