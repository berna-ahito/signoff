import pytest

from app.db.models import AuditLog, PurchaseRequest


def _make_request(db_session, requester_id: int, vendor_id: int, n: int) -> list[PurchaseRequest]:
    reqs = []
    for i in range(n):
        req = PurchaseRequest(
            title=f"Request {i}",
            description="A description with enough text",
            category="IT",
            urgency="low",
            quantity=1,
            estimated_cost=100.0,
            vendor_id=vendor_id,
            justification="Needed for work purposes",
            status="draft",
            requester_id=requester_id,
        )
        db_session.add(req)
        reqs.append(req)
    db_session.commit()
    return reqs


def _make_audit_logs(db_session, request_id: int, n: int) -> None:
    for i in range(n):
        log = AuditLog(
            request_id=request_id,
            actor_id=None,
            action=f"action_{i}",
            old_status="draft",
            new_status="pending_review",
        )
        db_session.add(log)
    db_session.commit()


# ---------------------------------------------------------------------------
# GET /requests/ pagination
# ---------------------------------------------------------------------------

class TestRequestsPagination:
    def test_envelope_shape(self, client, auth_headers, seed_users, db_session):
        from app.db.models import Vendor
        vendor = db_session.query(Vendor).first()
        _make_request(db_session, seed_users["alice"].id, vendor.id, 3)

        resp = client.get("/requests/", headers=auth_headers["alice"])
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {"items", "total", "skip", "limit"}
        assert data["total"] == 3
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert isinstance(data["items"], list)

    def test_skip_reduces_items(self, client, auth_headers, seed_users, db_session):
        from app.db.models import Vendor
        vendor = db_session.query(Vendor).first()
        _make_request(db_session, seed_users["alice"].id, vendor.id, 3)

        resp = client.get("/requests/?skip=1", headers=auth_headers["alice"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["skip"] == 1

    def test_limit_restricts_items(self, client, auth_headers, seed_users, db_session):
        from app.db.models import Vendor
        vendor = db_session.query(Vendor).first()
        _make_request(db_session, seed_users["alice"].id, vendor.id, 5)

        resp = client.get("/requests/?limit=2", headers=auth_headers["alice"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    def test_limit_over_100_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/requests/?limit=101", headers=auth_headers["alice"])
        assert resp.status_code == 422

    def test_skip_zero_and_limit_zero_invalid(self, client, auth_headers, seed_users):
        resp = client.get("/requests/?limit=0", headers=auth_headers["alice"])
        assert resp.status_code == 422

    def test_negative_skip_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/requests/?skip=-1", headers=auth_headers["alice"])
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/ pagination
# ---------------------------------------------------------------------------

class TestUsersPagination:
    def test_envelope_shape(self, client, auth_headers, seed_users):
        resp = client.get("/users/", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {"items", "total", "skip", "limit"}
        assert data["total"] == 4
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 4

    def test_skip_reduces_items(self, client, auth_headers, seed_users):
        resp = client.get("/users/?skip=1", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 3
        assert data["skip"] == 1

    def test_limit_restricts_items(self, client, auth_headers, seed_users):
        resp = client.get("/users/?limit=2", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    def test_limit_over_100_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/users/?limit=101", headers=auth_headers["admin"])
        assert resp.status_code == 422

    def test_negative_skip_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/users/?skip=-1", headers=auth_headers["admin"])
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /audit/ pagination
# ---------------------------------------------------------------------------

class TestAuditPagination:
    def _seed_audit_logs(self, db_session, seed_users, n: int) -> int:
        from app.db.models import Vendor
        vendor = db_session.query(Vendor).first()
        req = PurchaseRequest(
            title="Audit Test Request",
            description="Description text here long enough",
            category="IT",
            urgency="low",
            quantity=1,
            estimated_cost=50.0,
            vendor_id=vendor.id,
            justification="Needed for audit testing purposes",
            status="draft",
            requester_id=seed_users["alice"].id,
        )
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)
        _make_audit_logs(db_session, req.id, n)
        return req.id

    def test_envelope_shape(self, client, auth_headers, seed_users, db_session):
        self._seed_audit_logs(db_session, seed_users, 5)

        resp = client.get("/audit/", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {"items", "total", "skip", "limit"}
        assert data["total"] == 5
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert isinstance(data["items"], list)

    def test_skip_reduces_items(self, client, auth_headers, seed_users, db_session):
        self._seed_audit_logs(db_session, seed_users, 5)

        resp = client.get("/audit/?skip=2", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["skip"] == 2

    def test_limit_restricts_items(self, client, auth_headers, seed_users, db_session):
        self._seed_audit_logs(db_session, seed_users, 5)

        resp = client.get("/audit/?limit=3", headers=auth_headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["limit"] == 3

    def test_limit_over_100_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/audit/?limit=101", headers=auth_headers["admin"])
        assert resp.status_code == 422

    def test_negative_skip_returns_422(self, client, auth_headers, seed_users):
        resp = client.get("/audit/?skip=-1", headers=auth_headers["admin"])
        assert resp.status_code == 422
