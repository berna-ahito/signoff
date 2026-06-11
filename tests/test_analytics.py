"""
Analytics endpoints tests — TDD RED phase.

Tests for:
  GET /analytics/spend
  GET /analytics/categories
"""
import pytest
from sqlalchemy import text

from app.db.models import PurchaseRequest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_request(db, requester_id, category, urgency, cost, status="approved"):
    req = PurchaseRequest(
        title=f"Test {category}",
        description="Test description for procurement item",
        category=category,
        urgency=urgency,
        quantity=1,
        estimated_cost=cost,
        justification="Required for operations",
        status=status,
        requester_id=requester_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ===========================================================================
# GET /analytics/spend
# ===========================================================================

class TestSpendEndpoint:
    def test_spend_non_admin_returns_403(self, client, auth_headers, seed_users):
        """Any non-admin role must receive 403."""
        resp = client.get("/analytics/spend", headers=auth_headers["alice"])
        assert resp.status_code == 403

    def test_spend_non_admin_manager_returns_403(self, client, auth_headers, seed_users):
        resp = client.get("/analytics/spend", headers=auth_headers["bob"])
        assert resp.status_code == 403

    def test_spend_empty_returns_empty_list(self, client, auth_headers, seed_users):
        """No approved requests → empty list."""
        resp = client.get("/analytics/spend", headers=auth_headers["admin"])
        assert resp.status_code == 200
        assert resp.json() == []

    def test_spend_group_by_category_default(self, client, auth_headers, seed_users, db_session):
        """Default group_by=category, sorted by total desc."""
        alice = seed_users["alice"]
        _make_request(db_session, alice.id, "IT", "high", 100.0)
        _make_request(db_session, alice.id, "IT", "low", 200.0)
        _make_request(db_session, alice.id, "HR", "medium", 50.0)

        resp = client.get("/analytics/spend", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()

        assert len(data) == 2
        # Sorted descending by total
        assert data[0]["group"] == "IT"
        assert data[0]["count"] == 2
        assert data[0]["total_estimated_cost"] == pytest.approx(300.0)
        assert data[1]["group"] == "HR"
        assert data[1]["count"] == 1
        assert data[1]["total_estimated_cost"] == pytest.approx(50.0)

    def test_spend_explicit_group_by_category(self, client, auth_headers, seed_users, db_session):
        """Explicit group_by=category works same as default."""
        alice = seed_users["alice"]
        _make_request(db_session, alice.id, "IT", "high", 500.0)

        resp = client.get("/analytics/spend?group_by=category", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["group"] == "IT"
        assert data[0]["total_estimated_cost"] == pytest.approx(500.0)

    def test_spend_group_by_urgency(self, client, auth_headers, seed_users, db_session):
        """group_by=urgency groups correctly."""
        alice = seed_users["alice"]
        _make_request(db_session, alice.id, "IT", "high", 100.0)
        _make_request(db_session, alice.id, "HR", "high", 200.0)
        _make_request(db_session, alice.id, "IT", "low", 50.0)

        resp = client.get("/analytics/spend?group_by=urgency", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()

        groups = {item["group"]: item for item in data}
        assert "high" in groups
        assert "low" in groups
        assert groups["high"]["count"] == 2
        assert groups["high"]["total_estimated_cost"] == pytest.approx(300.0)
        assert groups["low"]["count"] == 1
        assert groups["low"]["total_estimated_cost"] == pytest.approx(50.0)
        # high has more total → first
        assert data[0]["group"] == "high"

    def test_spend_group_by_status(self, client, auth_headers, seed_users, db_session):
        """group_by=status — only approved requests appear in results."""
        alice = seed_users["alice"]
        _make_request(db_session, alice.id, "IT", "high", 100.0, status="approved")
        _make_request(db_session, alice.id, "HR", "low", 999.0, status="submitted")
        _make_request(db_session, alice.id, "Finance", "medium", 999.0, status="draft")

        resp = client.get("/analytics/spend?group_by=status", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()

        # Only approved rows should appear
        assert len(data) == 1
        assert data[0]["group"] == "approved"
        assert data[0]["count"] == 1
        assert data[0]["total_estimated_cost"] == pytest.approx(100.0)

    def test_spend_invalid_group_by_returns_400(self, client, auth_headers, seed_users):
        """Unknown group_by value returns 400."""
        resp = client.get("/analytics/spend?group_by=foobar", headers=auth_headers["admin"])
        assert resp.status_code == 400

    def test_spend_date_from_filter(self, client, auth_headers, seed_users, db_session):
        """date_from filters out older requests."""
        alice = seed_users["alice"]

        old = _make_request(db_session, alice.id, "IT", "high", 999.0)
        # Force old created_at
        db_session.execute(
            text("UPDATE purchase_requests SET created_at = '2020-01-01' WHERE id = :id"),
            {"id": old.id},
        )
        db_session.commit()

        _make_request(db_session, alice.id, "HR", "low", 50.0)

        resp = client.get("/analytics/spend?date_from=2024-01-01", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        groups = {item["group"]: item for item in data}
        assert "HR" in groups
        assert "IT" not in groups

    def test_spend_date_to_filter(self, client, auth_headers, seed_users, db_session):
        """date_to filters out newer requests (inclusive of the full day)."""
        alice = seed_users["alice"]

        old = _make_request(db_session, alice.id, "IT", "high", 100.0)
        db_session.execute(
            text("UPDATE purchase_requests SET created_at = '2020-06-15' WHERE id = :id"),
            {"id": old.id},
        )
        db_session.commit()

        _make_request(db_session, alice.id, "HR", "low", 999.0)

        resp = client.get("/analytics/spend?date_to=2020-12-31", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        groups = {item["group"]: item for item in data}
        assert "IT" in groups
        assert "HR" not in groups

    def test_spend_invalid_date_returns_400(self, client, auth_headers, seed_users):
        """Malformed date string returns 400."""
        resp = client.get("/analytics/spend?date_from=not-a-date", headers=auth_headers["admin"])
        assert resp.status_code == 400


# ===========================================================================
# GET /analytics/categories
# ===========================================================================

class TestCategoriesEndpoint:
    def test_categories_non_admin_returns_403(self, client, auth_headers, seed_users):
        """Any non-admin role must receive 403."""
        resp = client.get("/analytics/categories", headers=auth_headers["alice"])
        assert resp.status_code == 403

    def test_categories_non_admin_carol_returns_403(self, client, auth_headers, seed_users):
        resp = client.get("/analytics/categories", headers=auth_headers["carol"])
        assert resp.status_code == 403

    def test_categories_empty_returns_empty_list(self, client, auth_headers, seed_users):
        """No requests → empty list."""
        resp = client.get("/analytics/categories", headers=auth_headers["admin"])
        assert resp.status_code == 200
        assert resp.json() == []

    def test_categories_correct_aggregation(self, client, auth_headers, seed_users, db_session):
        """Verify counts and totals for approved/pending across categories."""
        alice = seed_users["alice"]

        # IT: 2 approved, 1 submitted
        _make_request(db_session, alice.id, "IT", "high", 100.0, status="approved")
        _make_request(db_session, alice.id, "IT", "low", 200.0, status="approved")
        _make_request(db_session, alice.id, "IT", "medium", 75.0, status="submitted")

        # HR: 1 approved, 1 draft
        _make_request(db_session, alice.id, "HR", "low", 50.0, status="approved")
        _make_request(db_session, alice.id, "HR", "high", 30.0, status="draft")

        # Finance: only rejected (not approved, not pending) — should still appear
        _make_request(db_session, alice.id, "Finance", "low", 999.0, status="rejected")

        resp = client.get("/analytics/categories", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()

        # All 3 distinct categories must appear
        assert len(data) == 3

        # Sorted alphabetically by category
        names = [item["category"] for item in data]
        assert names == sorted(names)

        by_cat = {item["category"]: item for item in data}

        # IT
        it = by_cat["IT"]
        assert it["approved_count"] == 2
        assert it["approved_total"] == pytest.approx(300.0)
        assert it["pending_count"] == 1
        assert it["pending_total"] == pytest.approx(75.0)

        # HR
        hr = by_cat["HR"]
        assert hr["approved_count"] == 1
        assert hr["approved_total"] == pytest.approx(50.0)
        assert hr["pending_count"] == 1
        assert hr["pending_total"] == pytest.approx(30.0)

        # Finance — rejected only; zeros for both buckets
        finance = by_cat["Finance"]
        assert finance["approved_count"] == 0
        assert finance["approved_total"] == pytest.approx(0.0)
        assert finance["pending_count"] == 0
        assert finance["pending_total"] == pytest.approx(0.0)

    def test_categories_pending_includes_draft_and_submitted(
        self, client, auth_headers, seed_users, db_session
    ):
        """pending_count includes both 'submitted' and 'draft' statuses."""
        alice = seed_users["alice"]
        _make_request(db_session, alice.id, "IT", "high", 10.0, status="draft")
        _make_request(db_session, alice.id, "IT", "low", 20.0, status="submitted")

        resp = client.get("/analytics/categories", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        it = data[0]
        assert it["category"] == "IT"
        assert it["approved_count"] == 0
        assert it["approved_total"] == pytest.approx(0.0)
        assert it["pending_count"] == 2
        assert it["pending_total"] == pytest.approx(30.0)

    def test_categories_sorted_alphabetically(self, client, auth_headers, seed_users, db_session):
        """Response is sorted alphabetically by category regardless of insertion order."""
        alice = seed_users["alice"]
        for cat in ["Zebra", "Apple", "Marketing", "Finance"]:
            _make_request(db_session, alice.id, cat, "low", 10.0, status="approved")

        resp = client.get("/analytics/categories", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        names = [item["category"] for item in data]
        assert names == ["Apple", "Finance", "Marketing", "Zebra"]
