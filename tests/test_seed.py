import subprocess
import sys

import pytest

from app.db.models import AIReview, ApprovalDecision, AuditLog, PurchaseRequest
from scripts import seed


def test_seed_all_creates_rich_purchase_requests(db_session, capsys):
    seed.seed_all(db_session, reset=False)

    requests = db_session.query(PurchaseRequest).all()
    assert len(requests) == 8

    statuses = [request.status for request in requests]
    assert statuses.count("approved") == 3
    assert statuses.count("pending_approval") == 2
    assert statuses.count("rejected") == 1
    assert statuses.count("needs_more_info") == 1
    assert statuses.count("draft") == 1

    approved_spend = sum(
        request.estimated_cost for request in requests if request.status == "approved"
    )
    pipeline_value = sum(request.estimated_cost for request in requests)
    assert approved_spend == pytest.approx(10540.00)
    assert pipeline_value == pytest.approx(38850.00)

    decisions = db_session.query(ApprovalDecision).all()
    assert len(decisions) == 5

    macbook = (
        db_session.query(PurchaseRequest)
        .filter(PurchaseRequest.title == "MacBook Pro M4 Pro x2 for Design Team")
        .one()
    )
    review = db_session.query(AIReview).filter(AIReview.request_id == macbook.id).one()
    assert review.risk_level == "medium"
    assert review.recommended_action == "review"
    assert "Missing: vendor quote attachment." in review.summary
    assert "Dear Apple Philippines" in review.rfq_draft

    desk = (
        db_session.query(PurchaseRequest)
        .filter(PurchaseRequest.title == "Standing Desk x4 for Engineering Team")
        .one()
    )
    transitions = (
        db_session.query(AuditLog)
        .filter(AuditLog.request_id == desk.id)
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert [(log.old_status, log.new_status) for log in transitions] == [
        ("draft", "pending_review"),
        ("pending_review", "pending_approval"),
        ("pending_approval", "approved"),
    ]

    output = capsys.readouterr().out
    assert "Seeded: 8 requests — 3 approved, 2 pending, 1 rejected, 1 needs_info, 1 draft" in output
    assert "Total approved spend: $10,540" in output
    assert "Total pipeline value: $38,850" in output


def test_seed_all_skips_when_requests_exist_without_reset(db_session, capsys):
    seed.seed_all(db_session, reset=False)
    seed.seed_all(db_session, reset=False)

    assert db_session.query(PurchaseRequest).count() == 8
    assert "Already seeded — run with --reset to reseed" in capsys.readouterr().out


def test_seed_script_is_executable_from_repo_root():
    result = subprocess.run(
        [sys.executable, "scripts/seed.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Seed ProcureFlow AI demo data." in result.stdout
