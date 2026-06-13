import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base, SessionLocal, engine
from app.db.models import (
    AIReview,
    ApprovalDecision,
    ApprovalRule,
    AuditLog,
    Department,
    PurchaseRequest,
    RefreshToken,
    RequestAttachment,
    User,
    Vendor,
)
from app.services.approval_engine import validate_transition
from app.services.audit_service import ACTION_DECISION, ACTION_ROUTED, ACTION_SUBMITTED, log_action


DEPARTMENT_NAMES = ["IT", "Finance", "Operations"]

VENDORS = [
    {"name": "Acme Corp", "contact_email": "sales@acme.com"},
    {"name": "TechSupply Ltd", "contact_email": "orders@techsupply.com"},
    {"name": "OfficeDepot PH", "contact_email": "enterprise@officedepot.ph"},
    {"name": "Apple Philippines", "contact_email": "business@apple.com"},
    {"name": "Adobe Systems", "contact_email": "teams@adobe.com"},
    {"name": "Slack Technologies", "contact_email": "sales@slack.com"},
]

USERS = [
    {
        "email": "alice@test.com",
        "password": "alice123",
        "full_name": "Alice Smith",
        "role": "requester",
        "dept": "IT",
    },
    {
        "email": "bob@test.com",
        "password": "bob123",
        "full_name": "Bob Jones",
        "role": "manager",
        "dept": "Operations",
    },
    {
        "email": "carol@test.com",
        "password": "carol123",
        "full_name": "Carol White",
        "role": "finance",
        "dept": "Finance",
    },
    {
        "email": "admin@test.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": "admin",
        "dept": "IT",
    },
]

APPROVAL_RULES = [
    {
        "name": "IT Equipment",
        "min_amount": 0,
        "max_amount": None,
        "category": "IT",
        "required_role": "manager",
        "priority": 5,
    },
    {
        "name": "Low Value Auto-Route",
        "min_amount": 0,
        "max_amount": 999.99,
        "category": None,
        "required_role": "manager",
        "priority": 10,
    },
    {
        "name": "High Value Finance Review",
        "min_amount": 1000,
        "max_amount": None,
        "category": None,
        "required_role": "finance",
        "priority": 20,
    },
]

REQUESTS = [
    {
        "title": "Standing Desk x4 for Engineering Team",
        "description": (
            "Engineers have been experiencing back issues. Requesting 4 sit-stand "
            "desks (Flexispot E7 Pro) to improve ergonomics and productivity."
        ),
        "category": "Facilities",
        "urgency": "medium",
        "quantity": 4,
        "estimated_cost": 2800.00,
        "vendor_name": "OfficeDepot PH",
        "justification": (
            "Medical recommendation from company nurse. Expected productivity gain "
            "of 15% based on published studies."
        ),
        "final_status": "approved",
        "assigned_role": "manager",
        "decision": {
            "approver": "bob@test.com",
            "value": "approved",
            "note": "Approved. Valid health justification, within budget.",
        },
        "days_ago": 9,
    },
    {
        "title": "MacBook Pro M4 Pro x2 for Design Team",
        "description": (
            "Current MacBook Pros are 4 years old and cannot run the latest design "
            "tools at adequate performance."
        ),
        "category": "IT",
        "urgency": "high",
        "quantity": 2,
        "estimated_cost": 6800.00,
        "vendor_name": "Apple Philippines",
        "justification": (
            "Design team's current machines take 45+ minutes to render complex "
            "prototypes. New machines would reduce this to 8 min."
        ),
        "final_status": "pending_approval",
        "assigned_role": "manager",
        "ai_review": {
            "risk_level": "medium",
            "summary": (
                "Request is well-justified with specific performance metrics. Cost "
                "is reasonable for professional hardware. Missing: vendor quote attachment."
            ),
            "recommended_action": "review",
            "rfq_draft": (
                "Dear Apple Philippines, We are requesting a formal quote for 2x "
                "MacBook Pro M4 Pro (16GB RAM, 512GB SSD) for enterprise use. "
                "Please include educational/enterprise pricing, AppleCare+, and "
                "estimated delivery timeline."
            ),
            "missing_info": ["vendor quote attachment"],
            "confidence": 0.84,
        },
        "days_ago": 7,
    },
    {
        "title": "Adobe Creative Cloud Team License — Annual",
        "description": (
            "Renewing 5-seat Adobe Creative Cloud license for the design and marketing team."
        ),
        "category": "Software",
        "urgency": "high",
        "quantity": 5,
        "estimated_cost": 4500.00,
        "vendor_name": "Adobe Systems",
        "justification": (
            "License expires in 30 days. Required for all ongoing client design projects."
        ),
        "final_status": "approved",
        "assigned_role": "finance",
        "decision": {
            "approver": "carol@test.com",
            "value": "approved",
            "note": "Renewal approved. Add to recurring budget line.",
        },
        "days_ago": 6,
    },
    {
        "title": "Espresso Machine for Office Kitchen",
        "description": "A quality espresso machine for the office break room.",
        "category": "Facilities",
        "urgency": "low",
        "quantity": 1,
        "estimated_cost": 850.00,
        "vendor_name": None,
        "justification": "Team morale. Many employees purchase coffee outside.",
        "final_status": "rejected",
        "assigned_role": "manager",
        "decision": {
            "approver": "bob@test.com",
            "value": "rejected",
            "note": "Not within budget this quarter. Revisit in Q3.",
        },
        "days_ago": 5,
    },
    {
        "title": "Cloud Storage Upgrade — AWS S3",
        "description": (
            "Our current S3 storage is at 89% capacity. Need to expand or migrate "
            "to a larger tier."
        ),
        "category": "IT",
        "urgency": "high",
        "quantity": 1,
        "estimated_cost": 1200.00,
        "vendor_name": None,
        "justification": (
            "Storage will hit 100% capacity within 3 weeks based on current growth rate."
        ),
        "final_status": "needs_more_info",
        "assigned_role": "finance",
        "decision": {
            "approver": "carol@test.com",
            "value": "needs_more_info",
            "note": (
                "Please provide: current storage usage breakdown by service, projected "
                "growth for next 6 months, and comparison with alternative providers "
                "(GCP, Azure)."
            ),
        },
        "days_ago": 4,
    },
    {
        "title": "Ergonomic Keyboard and Mouse Set x8",
        "description": (
            "Requesting ergonomic peripherals for the entire operations team to reduce RSI risk."
        ),
        "category": "IT",
        "urgency": "low",
        "quantity": 8,
        "estimated_cost": 960.00,
        "vendor_name": None,
        "justification": (
            "Draft request for ergonomic peripherals; final team roster still pending."
        ),
        "final_status": "draft",
        "assigned_role": None,
        "days_ago": 3,
    },
    {
        "title": "Office Renovation — Conference Room B",
        "description": (
            "Conference Room B needs AV upgrades and furniture replacement. Current "
            "setup is 8 years old."
        ),
        "category": "Facilities",
        "urgency": "medium",
        "quantity": 1,
        "estimated_cost": 18500.00,
        "vendor_name": None,
        "justification": (
            "Room is used for client meetings. Current setup creates a poor impression "
            "and has recurring AV failures."
        ),
        "final_status": "pending_approval",
        "assigned_role": "finance",
        "days_ago": 2,
    },
    {
        "title": "Slack Business+ Plan — Annual",
        "description": (
            "Upgrading from Slack Pro to Business+ for compliance message retention "
            "and guest account features."
        ),
        "category": "Software",
        "urgency": "medium",
        "quantity": 30,
        "estimated_cost": 3240.00,
        "vendor_name": "Slack Technologies",
        "justification": (
            "Legal team requires 90-day message retention for compliance. Current "
            "plan retains only 30 days."
        ),
        "final_status": "approved",
        "assigned_role": "manager",
        "decision": {
            "approver": "bob@test.com",
            "value": "approved",
            "note": "Approved. Legal requirement takes precedence.",
        },
        "days_ago": 1,
    },
]


def seed_departments(db):
    created = 0
    for name in DEPARTMENT_NAMES:
        if not db.query(Department).filter(Department.name == name).first():
            db.add(Department(name=name))
            created += 1
    db.commit()
    print(f"Seeded departments: {created}")
    return {department.name: department for department in db.query(Department).all()}


def seed_vendors(db):
    created = 0
    for vendor in VENDORS:
        if not db.query(Vendor).filter(Vendor.name == vendor["name"]).first():
            db.add(Vendor(**vendor))
            created += 1
    db.commit()
    print(f"Seeded vendors: {created}")
    return {vendor.name: vendor for vendor in db.query(Vendor).all()}


def seed_users(db, departments):
    created = 0
    for user_data in USERS:
        if not db.query(User).filter(User.email == user_data["email"]).first():
            department = departments.get(user_data["dept"])
            db.add(
                User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    department_id=department.id if department else None,
                    is_active=True,
                )
            )
            created += 1
    db.commit()
    print(f"Seeded users: {created}")
    return {user.email: user for user in db.query(User).all()}


def seed_approval_rules(db):
    created = 0
    for rule in APPROVAL_RULES:
        if not db.query(ApprovalRule).filter(ApprovalRule.name == rule["name"]).first():
            db.add(ApprovalRule(**rule))
            created += 1
    db.commit()
    print(f"Seeded approval rules: {created}")


def reset_seed_data(db):
    for model in (
        RequestAttachment,
        AIReview,
        AuditLog,
        ApprovalDecision,
        RefreshToken,
        PurchaseRequest,
    ):
        db.query(model).delete(synchronize_session=False)
    db.commit()


def _timestamp(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def _transition_request(db, request, actor_id, action, new_status, note=None, assigned_role=None):
    old_status = request.status
    validate_transition(old_status, new_status)
    request.status = new_status
    if assigned_role is not None:
        request.assigned_role = assigned_role
    request.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)
    log_action(db, request.id, actor_id, action, old_status, new_status, note)
    return request


def _add_ai_review(db, request, review_data):
    review = AIReview(
        request_id=request.id,
        provider_name=settings.ai_provider,
        summary=review_data["summary"],
        category=request.category,
        urgency="high" if request.urgency == "critical" else request.urgency,
        risk_level=review_data["risk_level"],
        missing_info=review_data["missing_info"],
        recommended_action=review_data["recommended_action"],
        rfq_draft=review_data["rfq_draft"],
        confidence=review_data["confidence"],
    )
    db.add(review)
    db.commit()


def seed_requests(db, users, vendors):
    for request_data in REQUESTS:
        created_at = _timestamp(request_data["days_ago"])
        vendor_name = request_data.get("vendor_name")
        vendor = vendors.get(vendor_name) if vendor_name else None
        request = PurchaseRequest(
            title=request_data["title"],
            description=request_data["description"],
            category=request_data["category"],
            urgency=request_data["urgency"],
            quantity=request_data["quantity"],
            estimated_cost=request_data["estimated_cost"],
            vendor_id=vendor.id if vendor else None,
            justification=request_data["justification"],
            status="draft",
            requester_id=users["alice@test.com"].id,
            assigned_role=None,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        if request_data["final_status"] != "draft":
            request = _transition_request(
                db,
                request,
                users["alice@test.com"].id,
                ACTION_SUBMITTED,
                "pending_review",
                "Submitted by requester.",
            )
            request = _transition_request(
                db,
                request,
                None,
                ACTION_ROUTED,
                "pending_approval",
                f"Routed to {request_data['assigned_role']} approval queue.",
                assigned_role=request_data["assigned_role"],
            )

        if request_data.get("decision"):
            decision = request_data["decision"]
            old_status = request.status
            final_status = request_data["final_status"]
            validate_transition(old_status, final_status)
            request.status = final_status
            request.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(request)
            approver = users[decision["approver"]]
            db.add(
                ApprovalDecision(
                    request_id=request.id,
                    actor_id=approver.id,
                    decision=decision["value"],
                    note=decision["note"],
                )
            )
            db.commit()
            log_action(db, request.id, approver.id, ACTION_DECISION, old_status, request.status, decision["note"])

        if request_data.get("ai_review"):
            _add_ai_review(db, request, request_data["ai_review"])

    requests = db.query(PurchaseRequest).all()
    approved_spend = sum(r.estimated_cost for r in requests if r.status == "approved")
    pipeline_value = sum(r.estimated_cost for r in requests)
    print("Seeded: 8 requests — 3 approved, 2 pending, 1 rejected, 1 needs_info, 1 draft")
    print(f"Total approved spend: {_format_money(approved_spend)}")
    print(f"Total pipeline value: {_format_money(pipeline_value)}")


def _format_money(value: float) -> str:
    return f"${value:,.0f}"


def seed_all(db, reset: bool = False):
    if reset:
        reset_seed_data(db)
    elif db.query(PurchaseRequest).count() > 0:
        print("Already seeded — run with --reset to reseed")
        return

    departments = seed_departments(db)
    vendors = seed_vendors(db)
    users = seed_users(db, departments)
    seed_approval_rules(db)
    seed_requests(db, users, vendors)
    print("Seed complete.")


def main():
    parser = argparse.ArgumentParser(description="Seed ProcureFlow AI demo data.")
    parser.add_argument("--reset", action="store_true", help="Delete request data and reseed.")
    args = parser.parse_args()

    if settings.app_env == "production":
        raise RuntimeError("Seed script must not be run directly in production")

    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed_all(db, reset=args.reset)
    finally:
        db.close()


if __name__ == "__main__":
    main()
