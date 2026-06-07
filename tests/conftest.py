import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.services.ai_review_service as _ai_svc
from app.core.limiter import limiter
from app.services.mock_ai_provider import MockAIProvider


@pytest.fixture(autouse=True)
def force_mock_provider(monkeypatch):
    monkeypatch.setattr(_ai_svc, "_provider", MockAIProvider())


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True

from app.core.security import get_password_hash
from app.db.base import Base, get_db
from app.db.models import Department, User, Vendor
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_users(db_session):
    dept = Department(name="IT")
    db_session.add(dept)
    db_session.flush()

    vendor = Vendor(name="TestVendor", contact_email="vendor@test.com")
    db_session.add(vendor)
    db_session.flush()

    alice = User(email="alice@test.com", hashed_password=get_password_hash("alice123"),
                 full_name="Alice Smith", role="requester", department_id=dept.id, is_active=True)
    bob = User(email="bob@test.com", hashed_password=get_password_hash("bob123"),
               full_name="Bob Jones", role="manager", department_id=dept.id, is_active=True)
    carol = User(email="carol@test.com", hashed_password=get_password_hash("carol123"),
                 full_name="Carol White", role="finance", department_id=dept.id, is_active=True)
    admin_user = User(email="admin@test.com", hashed_password=get_password_hash("admin123"),
                      full_name="Admin User", role="admin", department_id=dept.id, is_active=True)
    db_session.add_all([alice, bob, carol, admin_user])
    db_session.commit()
    for u in [alice, bob, carol, admin_user]:
        db_session.refresh(u)
    return {"alice": alice, "bob": bob, "carol": carol, "admin": admin_user}


@pytest.fixture
def auth_headers(client, seed_users):
    headers = {}
    creds = {
        "alice": ("alice@test.com", "alice123"),
        "bob": ("bob@test.com", "bob123"),
        "carol": ("carol@test.com", "carol123"),
        "admin": ("admin@test.com", "admin123"),
    }
    for name, (email, password) in creds.items():
        resp = client.post("/auth/login", json={"email": email, "password": password})
        token = resp.json()["access_token"]
        headers[name] = {"Authorization": f"Bearer {token}"}
    return headers
