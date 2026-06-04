import pytest
from fastapi.testclient import TestClient


def test_login_success_returns_token(client, seed_users):
    resp = client.post("/auth/login", json={"email": "alice@test.com", "password": "alice123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"].split(".")) == 3


def test_login_wrong_password_returns_401(client, seed_users):
    resp = client.post("/auth/login", json={"email": "alice@test.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client, seed_users):
    resp = client.post("/auth/login", json={"email": "nobody@test.com", "password": "anything"})
    assert resp.status_code == 401


def test_get_me_with_valid_token(client, seed_users, auth_headers):
    resp = client.get("/users/me", headers=auth_headers["alice"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice@test.com"
    assert data["role"] == "requester"


def test_get_me_without_token_returns_401(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_inactive_user_returns_403(client, seed_users, auth_headers, db_session):
    # Get token while active
    headers = auth_headers["alice"]
    # Deactivate alice
    alice = seed_users["alice"]
    alice.is_active = False
    db_session.commit()
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 403
