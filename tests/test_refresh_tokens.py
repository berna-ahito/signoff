"""Tests for Phase 2B: Refresh token system."""
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest

from app.db.models import RefreshToken


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _login(client, email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# 1. Login returns both tokens
# ---------------------------------------------------------------------------

def test_login_returns_refresh_token(client, seed_users):
    resp = _login(client, "alice@test.com", "alice123")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["refresh_token"]) > 20


# ---------------------------------------------------------------------------
# 2. /auth/refresh with a valid token issues a new access token
# ---------------------------------------------------------------------------

def test_refresh_issues_new_access_token(client, seed_users):
    login_resp = _login(client, "alice@test.com", "alice123")
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # refresh endpoint must NOT return a new refresh token
    assert "refresh_token" not in data


# ---------------------------------------------------------------------------
# 3. Garbage refresh token returns 401
# ---------------------------------------------------------------------------

def test_refresh_invalid_token_returns_401(client, seed_users):
    resp = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. Revoked refresh token (after logout) returns 401
# ---------------------------------------------------------------------------

def test_refresh_revoked_token_returns_401(client, seed_users):
    login_resp = _login(client, "alice@test.com", "alice123")
    refresh_token = login_resp.json()["refresh_token"]

    # Logout revokes the token
    logout_resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    # Now refreshing with the revoked token should fail
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 5. Logout returns 204
# ---------------------------------------------------------------------------

def test_logout_returns_204(client, seed_users):
    login_resp = _login(client, "bob@test.com", "bob123")
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# 6. Logout with garbage token returns 401
# ---------------------------------------------------------------------------

def test_logout_invalid_token_returns_401(client, seed_users):
    resp = client.post("/auth/logout", json={"refresh_token": "garbage-token-xyz"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 7. Expired refresh token returns 401
# ---------------------------------------------------------------------------

def test_expired_refresh_token_returns_401(client, seed_users, db_session):
    # Manually insert an expired RefreshToken row
    raw_token = "expired-test-token-value-123"
    intermediate = _sha256_hex(raw_token)
    token_hash = bcrypt.hashpw(intermediate.encode(), bcrypt.gensalt()).decode()
    past = datetime.now(timezone.utc) - timedelta(days=1)

    alice = seed_users["alice"]
    db_token = RefreshToken(
        user_id=alice.id,
        token_hash=token_hash,
        token_prefix=raw_token[:16],
        expires_at=past,
        revoked=False,
    )
    db_session.add(db_token)
    db_session.commit()

    resp = client.post("/auth/refresh", json={"refresh_token": raw_token})
    assert resp.status_code == 401
