from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import ApprovalRule, AuditLog, Department, PurchaseRequest, User, Vendor
from app.core.security import get_password_hash


def _add_manager_rule(db):
    db.add(
        ApprovalRule(
            name="Manager approval",
            min_amount=0,
            max_amount=None,
            category=None,
            required_role="manager",
            priority=10,
            is_active=True,
        )
    )
    db.commit()


def _request_body(**overrides):
    body = {
        "title": "Lifecycle Laptop",
        "description": "Laptop needed for engineering lifecycle tests",
        "category": "IT",
        "urgency": "medium",
        "quantity": 1,
        "estimated_cost": 800.0,
        "justification": "Required to run procurement control workflow tests",
    }
    body.update(overrides)
    return body


def _create_request(client, headers, **overrides):
    resp = client.post("/requests/", json=_request_body(**overrides), headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _approve_request(client, auth_headers, db_session, request_id):
    _add_manager_rule(db_session)
    submit = client.post(f"/requests/{request_id}/submit", headers=auth_headers["alice"])
    assert submit.status_code == 200
    decision = client.post(
        f"/approvals/{request_id}/decide",
        json={"decision": "approved", "note": "approved by manager"},
        headers=auth_headers["bob"],
    )
    assert decision.status_code == 200


def _create_approved_request(client, auth_headers, db_session, **overrides):
    request_data = _create_request(client, auth_headers["alice"], **overrides)
    _approve_request(client, auth_headers, db_session, request_data["id"])
    return request_data["id"]


def _create_purchase_order(client, auth_headers, request_id, **overrides):
    body = {
        "notes": "standard PO",
        "line_items": [
            {"description": "Laptop", "quantity": 1, "unit_price": 800.0},
        ],
    }
    body.update(overrides)
    resp = client.post(
        f"/requests/{request_id}/purchase-order",
        json=body,
        headers=auth_headers["carol"],
    )
    assert resp.status_code == 201
    return resp.json()


def _issue_purchase_order(client, auth_headers, po_id):
    resp = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "issued", "notes": "sent to vendor"},
        headers=auth_headers["carol"],
    )
    assert resp.status_code == 200
    return resp.json()


def _fully_receive_purchase_order(client, auth_headers, po_id):
    resp = client.post(
        f"/purchase-orders/{po_id}/receiving",
        json={"status": "fully_received", "note": "all items received"},
        headers=auth_headers["alice"],
    )
    assert resp.status_code == 201
    return resp.json()


def _create_and_verify_invoice(client, auth_headers, po_id, amount):
    invoice = client.post(
        f"/purchase-orders/{po_id}/invoices",
        json={"invoice_number": f"INV-{amount}", "invoice_amount": amount, "invoice_date": "2026-06-13"},
        headers=auth_headers["carol"],
    )
    assert invoice.status_code == 201
    verified = client.post(f"/invoices/{invoice.json()['id']}/verify", headers=auth_headers["carol"])
    assert verified.status_code == 200
    return verified.json()


def _make_second_requester(client, db_session, department_id):
    user = User(
        email="mallory@test.com",
        hashed_password=get_password_hash("mallory123"),
        full_name="Mallory Requester",
        role="requester",
        department_id=department_id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/auth/login", json={"email": "mallory@test.com", "password": "mallory123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_department_budget_summary_and_submit_warning(client, seed_users, auth_headers, db_session):
    department = db_session.get(Department, seed_users["alice"].department_id)
    department.monthly_budget = 1000.0
    db_session.commit()

    approved = PurchaseRequest(
        title="Approved spend",
        description="already approved spend",
        category="IT",
        urgency="low",
        quantity=1,
        estimated_cost=700.0,
        justification="existing approved spend",
        status="approved",
        requester_id=seed_users["alice"].id,
        department_id=department.id,
    )
    db_session.add(approved)
    db_session.commit()

    created = _create_request(client, auth_headers["alice"], estimated_cost=400.0)
    submit = client.post(f"/requests/{created['id']}/submit", headers=auth_headers["alice"])
    assert submit.status_code == 200
    assert submit.json()["budget_warning"] is not None

    summary = client.get(f"/departments/{department.id}/budget-summary", headers=auth_headers["carol"])
    assert summary.status_code == 200
    data = summary.json()
    assert data["monthly_budget"] == pytest.approx(1000.0)
    assert data["approved_spend_this_month"] == pytest.approx(700.0)
    assert data["pending_spend_this_month"] == pytest.approx(400.0)
    assert data["remaining_budget"] == pytest.approx(-100.0)
    assert data["over_budget"] is True

    audit = db_session.query(AuditLog).filter(AuditLog.request_id == created["id"], AuditLog.action == "budget_warning").one()
    assert "budget" in audit.note.lower()


def test_department_crud_rbac(client, seed_users, auth_headers):
    requester_list = client.get("/departments/", headers=auth_headers["alice"])
    assert requester_list.status_code == 403

    create = client.post(
        "/departments/",
        json={"name": "Operations", "code": "OPS", "monthly_budget": 2500.0},
        headers=auth_headers["admin"],
    )
    assert create.status_code == 201
    dept_id = create.json()["id"]

    finance_list = client.get("/departments/", headers=auth_headers["carol"])
    assert finance_list.status_code == 200
    assert any(item["code"] == "OPS" for item in finance_list.json())

    finance_patch = client.patch(
        f"/departments/{dept_id}",
        json={"monthly_budget": 3000.0},
        headers=auth_headers["carol"],
    )
    assert finance_patch.status_code == 403

    admin_patch = client.patch(
        f"/departments/{dept_id}",
        json={"monthly_budget": 3000.0, "is_active": False},
        headers=auth_headers["admin"],
    )
    assert admin_patch.status_code == 200
    assert admin_patch.json()["monthly_budget"] == pytest.approx(3000.0)
    assert admin_patch.json()["is_active"] is False


def test_vendor_crud_rbac_and_active_listing(client, seed_users, auth_headers):
    requester_create = client.post("/vendors/", json={"name": "Nope"}, headers=auth_headers["alice"])
    assert requester_create.status_code == 403

    create = client.post(
        "/vendors/",
        json={
            "name": "Acme Supplies",
            "contact_name": "Ann Buyer",
            "email": "ann@acme.com",
            "category": "IT",
            "payment_terms": "Net 30",
            "is_preferred": True,
            "notes": "Preferred laptop vendor",
        },
        headers=auth_headers["carol"],
    )
    assert create.status_code == 201
    vendor_id = create.json()["id"]

    list_resp = client.get("/vendors/", headers=auth_headers["alice"])
    assert list_resp.status_code == 200
    assert any(v["id"] == vendor_id for v in list_resp.json())

    patch = client.patch(f"/vendors/{vendor_id}", json={"is_active": False}, headers=auth_headers["admin"])
    assert patch.status_code == 200
    assert patch.json()["is_active"] is False

    inactive_detail = client.get(f"/vendors/{vendor_id}", headers=auth_headers["alice"])
    assert inactive_detail.status_code == 404


def test_purchase_order_creation_requires_approved_request(client, seed_users, auth_headers, db_session):
    draft = _create_request(client, auth_headers["alice"])
    blocked = client.post(
        f"/requests/{draft['id']}/purchase-order",
        json={"line_items": [{"description": "Laptop", "quantity": 1, "unit_price": 800.0}]},
        headers=auth_headers["carol"],
    )
    assert blocked.status_code == 400

    request_id = _create_approved_request(client, auth_headers, db_session)
    created = _create_purchase_order(client, auth_headers, request_id)
    assert created["po_number"].startswith("PF-")
    assert created["status"] == "draft"
    assert created["request_id"] == request_id
    assert created["line_items"][0]["total_price"] == pytest.approx(800.0)

    duplicate = client.post(
        f"/requests/{request_id}/purchase-order",
        json={"line_items": [{"description": "Laptop", "quantity": 1, "unit_price": 800.0}]},
        headers=auth_headers["carol"],
    )
    assert duplicate.status_code == 400


def test_purchase_order_creation_uses_procurement_request_access(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)

    requester_create = client.post(
        f"/requests/{request_id}/purchase-order",
        json={"line_items": [{"description": "Nope", "quantity": 1, "unit_price": 1.0}]},
        headers=auth_headers["alice"],
    )
    assert requester_create.status_code == 403

    manager_create = client.post(
        f"/requests/{request_id}/purchase-order",
        json={"line_items": [{"description": "Nope", "quantity": 1, "unit_price": 1.0}]},
        headers=auth_headers["bob"],
    )
    assert manager_create.status_code == 403

    finance_create = client.post(
        f"/requests/{request_id}/purchase-order",
        json={"line_items": [{"description": "Laptop", "quantity": 1, "unit_price": 800.0}]},
        headers=auth_headers["carol"],
    )
    assert finance_create.status_code == 201


def test_purchase_order_status_transition_rules_and_pdf_html(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    po = _create_purchase_order(client, auth_headers, request_id)

    bad_transition = client.patch(
        f"/purchase-orders/{po['id']}/status",
        json={"status": "closed", "notes": "too soon"},
        headers=auth_headers["carol"],
    )
    assert bad_transition.status_code == 400

    issued = client.patch(
        f"/purchase-orders/{po['id']}/status",
        json={"status": "issued", "notes": "sent to vendor"},
        headers=auth_headers["carol"],
    )
    assert issued.status_code == 200
    assert issued.json()["status"] == "issued"
    assert issued.json()["issued_at"] is not None

    requester_patch = client.patch(
        f"/purchase-orders/{po['id']}/status",
        json={"status": "vendor_confirmed"},
        headers=auth_headers["alice"],
    )
    assert requester_patch.status_code == 403

    pdf = client.get(f"/purchase-orders/{po['id']}/pdf", headers=auth_headers["carol"])
    assert pdf.status_code == 200
    assert "text/html" in pdf.headers["content-type"]
    assert po["po_number"] in pdf.text


def test_receiving_confirmation_moves_po_only_when_fully_received(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    po = _create_purchase_order(client, auth_headers, request_id)
    client.patch(f"/purchase-orders/{po['id']}/status", json={"status": "issued"}, headers=auth_headers["carol"])

    partial = client.post(
        f"/purchase-orders/{po['id']}/receiving",
        json={"status": "partially_received", "note": "one item pending"},
        headers=auth_headers["alice"],
    )
    assert partial.status_code == 201
    assert partial.json()["status"] == "partially_received"
    assert client.get(f"/purchase-orders/{po['id']}", headers=auth_headers["carol"]).json()["status"] == "issued"

    full = client.post(
        f"/purchase-orders/{po['id']}/receiving",
        json={"status": "fully_received", "note": "all items received"},
        headers=auth_headers["alice"],
    )
    assert full.status_code == 201
    assert client.get(f"/purchase-orders/{po['id']}", headers=auth_headers["carol"]).json()["status"] == "received"

    audit_count = db_session.query(AuditLog).filter(AuditLog.request_id == request_id, AuditLog.action == "receiving").count()
    assert audit_count == 2


def test_receiving_rejected_for_invalid_po_states(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    draft_po = _create_purchase_order(client, auth_headers, request_id)
    draft_receiving = client.post(
        f"/purchase-orders/{draft_po['id']}/receiving",
        json={"status": "fully_received", "note": "too early"},
        headers=auth_headers["alice"],
    )
    assert draft_receiving.status_code == 400

    cancelled_request_id = _create_approved_request(client, auth_headers, db_session)
    cancelled_po = _create_purchase_order(client, auth_headers, cancelled_request_id)
    cancel = client.patch(
        f"/purchase-orders/{cancelled_po['id']}/status",
        json={"status": "cancelled"},
        headers=auth_headers["carol"],
    )
    assert cancel.status_code == 200
    cancelled_receiving = client.post(
        f"/purchase-orders/{cancelled_po['id']}/receiving",
        json={"status": "fully_received", "note": "cancelled"},
        headers=auth_headers["alice"],
    )
    assert cancelled_receiving.status_code == 400

    received_request_id = _create_approved_request(client, auth_headers, db_session)
    received_po = _create_purchase_order(client, auth_headers, received_request_id)
    _issue_purchase_order(client, auth_headers, received_po["id"])
    _fully_receive_purchase_order(client, auth_headers, received_po["id"])
    duplicate_receiving = client.post(
        f"/purchase-orders/{received_po['id']}/receiving",
        json={"status": "fully_received", "note": "already received"},
        headers=auth_headers["alice"],
    )
    assert duplicate_receiving.status_code == 400

    closed_request_id = _create_approved_request(client, auth_headers, db_session)
    closed_po = _create_purchase_order(client, auth_headers, closed_request_id)
    _issue_purchase_order(client, auth_headers, closed_po["id"])
    _fully_receive_purchase_order(client, auth_headers, closed_po["id"])
    _create_and_verify_invoice(client, auth_headers, closed_po["id"], 800.0)
    close = client.patch(
        f"/purchase-orders/{closed_po['id']}/status",
        json={"status": "closed"},
        headers=auth_headers["carol"],
    )
    assert close.status_code == 200
    closed_receiving = client.post(
        f"/purchase-orders/{closed_po['id']}/receiving",
        json={"status": "fully_received", "note": "closed"},
        headers=auth_headers["alice"],
    )
    assert closed_receiving.status_code == 400


def test_receiving_accepted_for_issued_and_vendor_confirmed_pos(client, seed_users, auth_headers, db_session):
    issued_request_id = _create_approved_request(client, auth_headers, db_session)
    issued_po = _create_purchase_order(client, auth_headers, issued_request_id)
    _issue_purchase_order(client, auth_headers, issued_po["id"])
    issued_receiving = client.post(
        f"/purchase-orders/{issued_po['id']}/receiving",
        json={"status": "partially_received", "note": "first shipment"},
        headers=auth_headers["alice"],
    )
    assert issued_receiving.status_code == 201

    confirmed_request_id = _create_approved_request(client, auth_headers, db_session)
    confirmed_po = _create_purchase_order(client, auth_headers, confirmed_request_id)
    _issue_purchase_order(client, auth_headers, confirmed_po["id"])
    confirm = client.patch(
        f"/purchase-orders/{confirmed_po['id']}/status",
        json={"status": "vendor_confirmed"},
        headers=auth_headers["carol"],
    )
    assert confirm.status_code == 200
    confirmed_receiving = client.post(
        f"/purchase-orders/{confirmed_po['id']}/receiving",
        json={"status": "fully_received", "note": "complete"},
        headers=auth_headers["alice"],
    )
    assert confirmed_receiving.status_code == 201
    assert client.get(f"/purchase-orders/{confirmed_po['id']}", headers=auth_headers["carol"]).json()["status"] == "received"


def test_invoice_verification_matched_and_mismatch(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    po = _create_purchase_order(client, auth_headers, request_id)

    matched = client.post(
        f"/purchase-orders/{po['id']}/invoices",
        json={"invoice_number": "INV-1", "invoice_amount": 800.0, "invoice_date": "2026-06-13"},
        headers=auth_headers["carol"],
    )
    assert matched.status_code == 201
    verify_matched = client.post(f"/invoices/{matched.json()['id']}/verify", headers=auth_headers["carol"])
    assert verify_matched.status_code == 200
    assert verify_matched.json()["status"] == "matched"

    mismatch = client.post(
        f"/purchase-orders/{po['id']}/invoices",
        json={"invoice_number": "INV-2", "invoice_amount": 900.0, "invoice_date": "2026-06-13"},
        headers=auth_headers["carol"],
    )
    assert mismatch.status_code == 201
    verify_mismatch = client.post(f"/invoices/{mismatch.json()['id']}/verify", headers=auth_headers["carol"])
    assert verify_mismatch.status_code == 200
    assert verify_mismatch.json()["status"] == "mismatch"

    requester_verify = client.post(f"/invoices/{mismatch.json()['id']}/verify", headers=auth_headers["alice"])
    assert requester_verify.status_code == 403


def test_closeout_requires_received_po_and_acceptable_invoice(client, seed_users, auth_headers, db_session):
    no_invoice_request_id = _create_approved_request(client, auth_headers, db_session)
    no_invoice_po = _create_purchase_order(client, auth_headers, no_invoice_request_id)
    _issue_purchase_order(client, auth_headers, no_invoice_po["id"])
    _fully_receive_purchase_order(client, auth_headers, no_invoice_po["id"])
    close_no_invoice = client.patch(
        f"/purchase-orders/{no_invoice_po['id']}/status",
        json={"status": "closed"},
        headers=auth_headers["carol"],
    )
    assert close_no_invoice.status_code == 400

    mismatch_request_id = _create_approved_request(client, auth_headers, db_session)
    mismatch_po = _create_purchase_order(client, auth_headers, mismatch_request_id)
    _issue_purchase_order(client, auth_headers, mismatch_po["id"])
    _fully_receive_purchase_order(client, auth_headers, mismatch_po["id"])
    _create_and_verify_invoice(client, auth_headers, mismatch_po["id"], 900.0)
    close_mismatch = client.patch(
        f"/purchase-orders/{mismatch_po['id']}/status",
        json={"status": "closed"},
        headers=auth_headers["carol"],
    )
    assert close_mismatch.status_code == 400

    matched_request_id = _create_approved_request(client, auth_headers, db_session)
    matched_po = _create_purchase_order(client, auth_headers, matched_request_id)
    _issue_purchase_order(client, auth_headers, matched_po["id"])
    _fully_receive_purchase_order(client, auth_headers, matched_po["id"])
    _create_and_verify_invoice(client, auth_headers, matched_po["id"], 800.0)
    close_matched = client.patch(
        f"/purchase-orders/{matched_po['id']}/status",
        json={"status": "closed"},
        headers=auth_headers["carol"],
    )
    assert close_matched.status_code == 200
    assert close_matched.json()["status"] == "closed"


def test_mismatch_invoice_requires_finance_approval_note_before_closeout(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    po = _create_purchase_order(client, auth_headers, request_id)
    _issue_purchase_order(client, auth_headers, po["id"])
    _fully_receive_purchase_order(client, auth_headers, po["id"])
    mismatch = _create_and_verify_invoice(client, auth_headers, po["id"], 900.0)
    assert mismatch["status"] == "mismatch"

    requester_approval = client.post(
        f"/invoices/{mismatch['id']}/approve-payment",
        json={"note": "requester should not approve"},
        headers=auth_headers["alice"],
    )
    assert requester_approval.status_code == 403

    missing_note = client.post(
        f"/invoices/{mismatch['id']}/approve-payment",
        json={"note": "   "},
        headers=auth_headers["carol"],
    )
    assert missing_note.status_code in (400, 422)

    approved = client.post(
        f"/invoices/{mismatch['id']}/approve-payment",
        json={"note": "Finance approved variance after vendor confirmation"},
        headers=auth_headers["carol"],
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved_for_payment"

    close = client.patch(
        f"/purchase-orders/{po['id']}/status",
        json={"status": "closed"},
        headers=auth_headers["carol"],
    )
    assert close.status_code == 200
    assert close.json()["status"] == "closed"


def test_vendor_id_validation_on_request_create_update_and_po_create(client, seed_users, auth_headers, db_session):
    invalid_create = client.post("/requests/", json=_request_body(vendor_id=99999), headers=auth_headers["alice"])
    assert invalid_create.status_code in (400, 404)

    inactive_vendor = Vendor(name="Inactive Vendor", is_active=False)
    db_session.add(inactive_vendor)
    db_session.commit()
    db_session.refresh(inactive_vendor)

    inactive_create = client.post(
        "/requests/",
        json=_request_body(vendor_id=inactive_vendor.id),
        headers=auth_headers["alice"],
    )
    assert inactive_create.status_code == 400

    draft = _create_request(client, auth_headers["alice"])
    invalid_update = client.patch(
        f"/requests/{draft['id']}",
        json={"vendor_id": 99999},
        headers=auth_headers["alice"],
    )
    assert invalid_update.status_code in (400, 404)

    inactive_update = client.patch(
        f"/requests/{draft['id']}",
        json={"vendor_id": inactive_vendor.id},
        headers=auth_headers["alice"],
    )
    assert inactive_update.status_code == 400

    approved_request_id = _create_approved_request(client, auth_headers, db_session)
    invalid_po_vendor = client.post(
        f"/requests/{approved_request_id}/purchase-order",
        json={
            "vendor_id": 99999,
            "line_items": [{"description": "Laptop", "quantity": 1, "unit_price": 800.0}],
        },
        headers=auth_headers["carol"],
    )
    assert invalid_po_vendor.status_code in (400, 404)

    inactive_po_vendor = client.post(
        f"/requests/{approved_request_id}/purchase-order",
        json={
            "vendor_id": inactive_vendor.id,
            "line_items": [{"description": "Laptop", "quantity": 1, "unit_price": 800.0}],
        },
        headers=auth_headers["carol"],
    )
    assert inactive_po_vendor.status_code == 400


def test_comments_visibility_and_audit(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)

    public = client.post(
        f"/requests/{request_id}/comments",
        json={"body": "Can you clarify delivery timing?", "visibility": "public"},
        headers=auth_headers["bob"],
    )
    assert public.status_code == 201

    internal = client.post(
        f"/requests/{request_id}/comments",
        json={"body": "Finance-only payment concern", "visibility": "finance_internal"},
        headers=auth_headers["admin"],
    )
    assert internal.status_code == 201

    requester_internal = client.post(
        f"/requests/{request_id}/comments",
        json={"body": "I should not mark this internal", "visibility": "finance_internal"},
        headers=auth_headers["alice"],
    )
    assert requester_internal.status_code == 403

    alice_view = client.get(f"/requests/{request_id}/comments", headers=auth_headers["alice"])
    assert alice_view.status_code == 200
    assert [c["visibility"] for c in alice_view.json()] == ["public"]

    finance_view = client.get(f"/requests/{request_id}/comments", headers=auth_headers["admin"])
    assert finance_view.status_code == 200
    assert {c["visibility"] for c in finance_view.json()} == {"public", "finance_internal"}

    assert db_session.query(AuditLog).filter(AuditLog.request_id == request_id, AuditLog.action == "comment").count() == 2


def test_overdue_request_query_and_response_field(client, seed_users, auth_headers, db_session):
    overdue = PurchaseRequest(
        title="Overdue approval",
        description="This request is overdue",
        category="IT",
        urgency="high",
        quantity=1,
        estimated_cost=500.0,
        justification="Needed urgently",
        status="pending_approval",
        assigned_role="manager",
        requester_id=seed_users["alice"].id,
        department_id=seed_users["alice"].department_id,
        submitted_at=datetime.now(timezone.utc) - timedelta(days=5),
        approval_due_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(overdue)
    db_session.commit()

    requester_resp = client.get("/requests/overdue", headers=auth_headers["alice"])
    assert requester_resp.status_code == 403

    manager_resp = client.get("/requests/overdue", headers=auth_headers["bob"])
    assert manager_resp.status_code == 200
    assert manager_resp.json()["items"][0]["id"] == overdue.id
    assert manager_resp.json()["items"][0]["overdue"] is True


def test_idor_on_new_request_po_invoice_scoped_endpoints(client, seed_users, auth_headers, db_session):
    request_id = _create_approved_request(client, auth_headers, db_session)
    po = _create_purchase_order(client, auth_headers, request_id)
    invoice = client.post(
        f"/purchase-orders/{po['id']}/invoices",
        json={"invoice_number": "INV-IDOR", "invoice_amount": 800.0, "invoice_date": "2026-06-13"},
        headers=auth_headers["carol"],
    ).json()

    other_headers = _make_second_requester(client, db_session, seed_users["alice"].department_id)

    assert client.get(f"/requests/{request_id}/comments", headers=other_headers).status_code == 403
    assert client.post(
        f"/requests/{request_id}/comments",
        json={"body": "No access", "visibility": "public"},
        headers=other_headers,
    ).status_code == 403
    assert client.post(
        f"/requests/{request_id}/purchase-order",
        json={"line_items": [{"description": "Nope", "quantity": 1, "unit_price": 1.0}]},
        headers=auth_headers["alice"],
    ).status_code == 403
    assert client.get(f"/purchase-orders/{po['id']}", headers=other_headers).status_code == 403
    assert client.post(
        f"/purchase-orders/{po['id']}/receiving",
        json={"status": "fully_received", "note": "No access"},
        headers=other_headers,
    ).status_code == 403
    assert client.get(f"/purchase-orders/{po['id']}/invoices", headers=auth_headers["alice"]).status_code == 403
    assert client.post(f"/invoices/{invoice['id']}/verify", headers=auth_headers["alice"]).status_code == 403
