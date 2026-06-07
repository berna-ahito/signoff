import os
if os.getenv("APP_ENV") == "production":
    raise RuntimeError("Seed script must not run in production")

from app.db.base import Base, SessionLocal, engine
from app.db.models import ApprovalRule, Department, User, Vendor
from app.core.security import get_password_hash


def seed_departments(db):
    names = ["IT", "Finance", "Operations"]
    created = 0
    for name in names:
        if not db.query(Department).filter(Department.name == name).first():
            db.add(Department(name=name))
            created += 1
    db.commit()
    print(f"Seeded departments: {created}")
    return {d.name: d for d in db.query(Department).all()}


def seed_vendors(db):
    vendors = [
        {"name": "Acme Corp", "contact_email": "sales@acme.com"},
        {"name": "TechSupply Ltd", "contact_email": "orders@techsupply.com"},
    ]
    created = 0
    for v in vendors:
        if not db.query(Vendor).filter(Vendor.name == v["name"]).first():
            db.add(Vendor(**v))
            created += 1
    db.commit()
    print(f"Seeded vendors: {created}")


def seed_users(db, departments):
    users = [
        {"email": "alice@test.com", "password": "alice123", "full_name": "Alice Smith", "role": "requester", "dept": "IT"},
        {"email": "bob@test.com", "password": "bob123", "full_name": "Bob Jones", "role": "manager", "dept": "Operations"},
        {"email": "carol@test.com", "password": "carol123", "full_name": "Carol White", "role": "finance", "dept": "Finance"},
        {"email": "admin@test.com", "password": "admin123", "full_name": "Admin User", "role": "admin", "dept": "IT"},
    ]
    created = 0
    for u in users:
        if not db.query(User).filter(User.email == u["email"]).first():
            dept = departments.get(u["dept"])
            db.add(User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                department_id=dept.id if dept else None,
                is_active=True,
            ))
            created += 1
    db.commit()
    print(f"Seeded users: {created}")


def seed_approval_rules(db):
    rules = [
        {"name": "IT Equipment", "min_amount": 0, "max_amount": None, "category": "IT", "required_role": "manager", "priority": 5},
        {"name": "Low Value Auto-Route", "min_amount": 0, "max_amount": 999.99, "category": None, "required_role": "manager", "priority": 10},
        {"name": "High Value Finance Review", "min_amount": 1000, "max_amount": None, "category": None, "required_role": "finance", "priority": 20},
    ]
    created = 0
    for r in rules:
        if not db.query(ApprovalRule).filter(ApprovalRule.name == r["name"]).first():
            db.add(ApprovalRule(**r))
            created += 1
    db.commit()
    print(f"Seeded approval rules: {created}")


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        depts = seed_departments(db)
        seed_vendors(db)
        seed_users(db, depts)
        seed_approval_rules(db)
        print("Seed complete.")
    finally:
        db.close()
